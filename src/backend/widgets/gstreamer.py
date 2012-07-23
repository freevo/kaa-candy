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

__all__ = [ 'Gstreamer' ]

# Python imports
import os
import sys

# Clutter and GStreamer GI bindings
from gi.repository import Clutter as clutter, ClutterGst, Gst as gst

import kaa.metadata
import widget

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

class Gstreamer(widget.Widget):
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
        self.obj = ClutterGst.VideoTexture()
        self.obj.set_seek_flags(ClutterGst.SeekFlags(1))
        self.obj.connect("notify::progress", self.event_progress)
        self.obj.connect("eos", self.event_finished)
        self.obj.connect_after("size-change", self.event_size_change)
        if self.audio_only:
            # audio element
            if self.visualisation:
                pipeline = self.obj.get_pipeline()
                flags = pipeline.get_property('flags')
                pipeline.set_property('flags', flags | 0x00000008)
            else:
                self.obj.hide()

    def update(self, modified):
        """
        Render the widget
        """
        super(Gstreamer, self).update(modified)
        if 'width' in modified or 'height' in modified or 'x' in modified or 'y' in modified:
            self.calculate_geometry()
        if 'url' in modified and self.url:
            self.obj.set_filename(self.url)
            streaminfo = {
                'audio': {},
                'subtitle': {},
                'is_menu': False,
                'sync': True
            }
            metadata = kaa.metadata.parse(self.url)
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
        self.obj.set_playing(True)

    def do_stop(self):
        """
        Stop playback
        """
        self.obj.set_playing(False)
        self.obj.set_filename('')
        self.send_widget_event('finished')

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_pause(self):
        """
        Pause playback
        """
        self.obj.set_playing(False)

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_resume(self):
        """
        Resume playback
        """
        self.obj.set_playing(True)
        # Seek nowhere. This is kind of stupid but clutter-gst does
        # not resume playback unless you seek. This is a bug I have to
        # check if it is fixed in the latest version and report it if
        # not.
        self.do_seek(0, SEEK_RELATIVE)

    @requires_state(gst.State.PLAYING, gst.State.PAUSED)
    def do_seek(self, value, type):
        """
        Seek to the given position
        """
        if type == SEEK_PERCENTAGE:
            pos = value / 100.0
        else:
            if not self.obj.get_duration():
                return
            if type == SEEK_RELATIVE:
                pos = self.obj.get_progress() + (1.0 / self.obj.get_duration()) * value
            if type == SEEK_ABSOLUTE:
                pos = (1.0 / self.obj.get_duration()) * value
        self.obj.set_progress(max(min(pos, 1.0), 0))

    @requires_state(gst.State.PLAYING)
    def do_set_audio(self, idx):
        """
        Set the audio stream
        """
        self.obj.set_audio_stream(idx)

    def do_set_subtitle(self, idx):
        """
        Set the subtitle stream (-1 == none)
        """
        self.obj.set_subtitle_track(idx)

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

    def do_nav_command(self, cmd):
        """
        Send DVD navigation command
        """
        pass

    #
    # events from gstreamer
    #

    def event_size_change(self, texture, base_width, base_height):
        self.aspect = self.original_aspect = float(base_width) / base_height
        self.zoom = 1
        self.calculate_geometry()

    def event_progress(self, media, pspec):
        """
        Progress update
        """
        if self.state in (gst.State.PLAYING, gst.State.PAUSED):
            pos = media.get_progress() * media.get_duration()
            self.send_widget_event('progress', pos)
            return
        # FIXME: we should not use the progress signal here and use
        # the correct one for state changes. But I cannot find the
        # signal used for state changes :(
        state_change_return, state = media.get_pipeline().get_state(0)[:2]
        if state_change_return != gst.StateChangeReturn.SUCCESS:
            return
        self.state = state
        if not self.delayed:
            return
        for delayed in self.delayed[:]:
            if self.state in delayed[0]:
                func, args, kwargs = delayed[1:]
                func(self, *args, **kwargs)
                self.delayed.remove(delayed)

    def event_finished(self, media):
        """
        Finished event
        """
        self.send_widget_event('finished')

# initialize gstreamer
ClutterGst.init(sys.argv)
