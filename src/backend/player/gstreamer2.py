# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# video.py - gstreamer video widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# The widget does not use kaa.popcorn because gstreamer using
# kaa.candy and mplayer are too different to add support to
# kaa.popcorn without rewriting too much. Furthermore, kaa.popcorn
# seems to have a raise condition I cannot find and is too complex;
# much is not needed.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2012 Dirk Meyer
#
# Based on various previous attempts to create a canvas system for
# Freevo by Dirk Meyer and Jason Tackaberry.  Please see the file
# AUTHORS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

# Python imports
import os
import sys
import gi

# Clutter and GStreamer GI bindings
from gi.repository import Clutter as clutter, ClutterGst, Gst as gst, GObject as gobject

if ClutterGst.MAJOR_VERSION != 2:
    raise RuntimeError('wrong version')

import kaa.metadata
import candy

def requires_state(*states):
    """
    Small internal state maschine for gstreamer calls from the
    frontend.
    """
    def decorator(func):
        def newfunc(self, *args, **kwargs):
            if not self.state in states:
                return self.delayed.append((states, func, args, kwargs))
            return func(self, *args, **kwargs)
        return newfunc
    return decorator

SEEK_RELATIVE = 'SEEK_RELATIVE'
SEEK_ABSOLUTE = 'SEEK_ABSOLUTE'
SEEK_PERCENTAGE = 'SEEK_PERCENTAGE'

ASPECT_ORIGINAL = 'ASPECT_ORIGINAL'
ASPECT_16_9 = 'ASPECT_16_9'
ASPECT_4_3 = 'ASPECT_4_3'
ASPECT_ZOOM = 'ASPECT_ZOOM'

class Player(candy.Widget):
    """
    Gstreamer video widget.
    """

    state = gst.State.NULL
    aspect = original_aspect = None
    zoom = 1

    def create(self):
        """
        Create the clutter object
        """
        self.delayed = []
        self.obj = clutter.Texture()
        self.obj.hide()

    def update(self, modified):
        """
        Render the widget
        """
        if 'width' in modified or 'height' in modified:
            if 'width' in modified and self.width:
                self.obj.set_width(self.width)
            if 'height' in modified and self.height:
                self.obj.set_height(self.height)
            self.calculate_geometry()
        if 'uri' in modified and self.uri:
            self.pipeline = gst.ElementFactory.make('playbin', 'pipeline')
            # There is a memory problem somehow. If we loose the sink
            # here gstreamer does not has a ref on its own and it
            # crashes. If we just keep the ref until the widget is
            # destroyed, it dies at that point (or later when we
            # repeat this). Even storing the sink forever crashes
            # gstreamer with gobject messages at some point. Maybe I'm
            # doing something wrong here, but I don't think so.
            sink = gst.ElementFactory.make('cluttersink', 'video')
            sink.set_property('texture', self.obj)
            self.pipeline.set_property('video-sink', sink)
            if self.uri.endswith('/'):
                self.uri = self.uri[:-1]
            if self.uri.find('://') == -1:
                self.uri = 'file://' + self.uri
            self.pipeline.set_property("uri", self.uri)
            streaminfo = {
                'audio': {},
                'subtitle': {},
                'is_menu': False,
                'sync': True
            }
            if self.uri.startswith('file://'):
                metadata = kaa.metadata.parse(self.uri)
                if metadata and 'audio' in metadata:
                    # video item, not audio only
                    for audio in metadata.audio:
                        streaminfo['audio'][audio.id] = None if audio.langcode == 'und' else audio.langcode
                    for sub in metadata.subtitles:
                        streaminfo['subtitle'][sub.id] = None if sub.langcode == 'und' else sub.langcode
            self.send_widget_event('streaminfo', streaminfo)


    def calculate_geometry(self, secs=0):
        """
        Calculate geometry values based on requested geometry and aspect
        """
        if not self.aspect:
            return
        width, height = self.width * self.zoom, self.height * self.zoom
        if int(height * self.aspect) > width:
            height = int(width / self.aspect)
        else:
            width = int(height * self.aspect)
        x = self.x + int(self.width - width) / 2
        y = self.y + int(self.height - height) / 2
        self.obj.animatev(clutter.AnimationMode.EASE_IN_QUAD, int(secs * 1000) or 1,
             ['x', 'y', 'width', 'height'], [x,y,width, height])

    #
    # control callbacks from the main process
    #

    def do_play(self):
        """
        Start playback
        """
        if not self.pipeline:
            return
        self.pipeline.set_state(gst.State.PLAYING)
        gobject.timeout_add(500, self.event_progress)

    def do_stop(self):
        """
        Stop playback
        """
        if not self.pipeline:
            return
        self.pipeline.set_state(gst.State.NULL)
        self.pipeline = None
        self.send_widget_event('finished')

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_pause(self):
        """
        Pause playback
        """
        if not self.pipeline:
            return
        self.pipeline.set_state(gst.State.PAUSED)

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_resume(self):
        """
        Resume playback
        """
        if not self.pipeline:
            return
        self.pipeline.set_state(gst.State.PLAYING)

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_seek(self, value, type):
        """
        Seek to the given position
        """
        # Code broken
        return
        if type == SEEK_PERCENTAGE:
            pos = value / 100.0
        else:
            duration = self.pipeline.query_duration(gst.Format.TIME)[1]
            if not duration:
                return
            current = self.pipeline.query_position(gst.Format.TIME)[1]
            if type == SEEK_RELATIVE:
                newpos = current + value * gst.SECOND
            if type == SEEK_ABSOLUTE:
                newpos = value * gst.SECOND
        self.pipeline.seek_simple(gst.Format.TIME, gst.SeekFlags.FLUSH | gst.SeekFlags.KEY_UNIT, newpos)

    @requires_state(gst.State.PLAYING)
    def do_set_audio(self, idx):
        """
        Set the audio stream
        """
        if not self.pipeline:
            return
        self.pipeline.set_property('current-audio', idx)

    @requires_state(gst.State.PLAYING)
    def do_set_subtitle(self, idx):
        """
        Set the subtitle stream (-1 == none)
        """
        pass

    def do_set_aspect(self, aspect):
        """
        Set the aspect ratio
        """
        if aspect == ASPECT_ORIGINAL:
            self.zoom = 1
            self.aspect = self.original_aspect
        if aspect == ASPECT_16_9:
            self.zoom = 1
            self.aspect = 16.0 / 9
        if aspect == ASPECT_4_3:
            self.zoom = 1
            self.aspect = 4.0 / 3
        if aspect == ASPECT_ZOOM:
            self.aspect = 4.0 / 3
            self.zoom = 4.0 / 3
        self.calculate_geometry(0.2)

    def do_set_deinterlace(self, value):
        """
        Turn on/off deinterlacing
        """
        pass

    def do_nav_command(self, cmd):
        """
        Send DVD navigation command
        """
        pass

    #
    # events from gstreamer
    #

    def event_size_change(self, texture, base_width, base_height):
        if self.audio_only and self.visualisation:
            return
        self.aspect = self.original_aspect = float(base_width) / base_height
        self.zoom = 1
        self.calculate_geometry()

    def event_progress(self):
        """
        Progress update
        """
        if not self.pipeline:
            return False
        if self.state in (gst.State.PLAYING, gst.State.PAUSED):
            pos = float(self.pipeline.query_position(gst.Format.TIME)[1]) / 1000000000
            self.send_widget_event('progress', pos)
            return True
        # FIXME: we should not use the progress signal here and use
        # the correct one for state changes. But I cannot find the
        # signal used for state changes :(
        state_change_return, state = self.pipeline.get_state(0)[:2]
        if state_change_return != gst.StateChangeReturn.SUCCESS:
            return True
        if not self.state in (gst.State.PLAYING, gst.State.PAUSED) and \
                state in (gst.State.PLAYING, gst.State.PAUSED):
            caps = self.pipeline.emit('get-video-pad', 0)
            s = caps.get_current_caps().get_structure(0)
            width = s.get_int('width')[1]
            height = s.get_int('height')[1]
            # Resize and move the texture to keep the aspect
            # ratio. This is kind of ugly because when the application
            # changes it this calculation won't happen again. And I
            # guess we should also connect to cap changes to redo this
            # calculations. Besides that, it should be possible to
            # change the aspect ratio during playback time,
            # e.g. ignore it and zoom.
            a1, a2 = s.get_fraction('pixel-aspect-ratio')[1:]
            aspect = (float(width) / height) * (float(a1) / a2)
            if int(self.height * aspect) > self.width:
                height = int(self.width / aspect)
                self.obj.set_y(self.y + int(self.height - height) / 2)
                self.obj.set_height(height)
            else:
                width = int(self.height * aspect)
                self.obj.set_x(self.x + int(self.width - width) / 2)
                self.obj.set_width(width)
            # Something else that could be interessting in the future:
            # s.get_boolean('interlaced')
            self.obj.show()
        self.state = state
        if not self.delayed:
            return True
        for delayed in self.delayed[:]:
            if self.state in delayed[0]:
                func, args, kwargs = delayed[1:]
                func(self, *args, **kwargs)
                self.delayed.remove(delayed)
        return True

    def event_finished(self, media):
        """
        Finished event
        """
        self.send_widget_event('finished')

# initialize gstreamer
ClutterGst.init(sys.argv)
