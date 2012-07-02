# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# video.py - gstreamer video widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# THIS WIDGET DOES NOT WORK DUE TO REFERENCE PROBLEMS IN THE PIPELINE
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2012 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Based on various previous attempts to create a canvas system for
# Freevo by Dirk Meyer and Jason Tackaberry.  Please see the file
# AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------

__all__ = [ 'Gstreamer2' ]

# Python imports
import os
import sys

# Clutter and GStreamer GI bindings
from gi.repository import Clutter as clutter, ClutterGst, Gst as gst, GObject as gobject

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

class Gstreamer2(widget.Widget):
    """
    Gstreamer video widget.
    """

    state = gst.State.NULL
    pipeline = None

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
        super(Gstreamer2, self).update(modified)
        if 'url' in modified and self.url:
            self.pipeline = gst.ElementFactory.make('playbin2', 'pipeline')
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
            if self.url.endswith('/'):
                self.url = self.url[:-1]
            if self.url.find('://') == -1:
                self.url = 'file://' + self.url
            self.pipeline.set_property("uri", self.url)

            # self.obj.set_seek_flags(ClutterGst.SeekFlags(1))
            # self.obj.connect("eos", self.event_finished)
            # if self.audio_only:
            #     # audio element
            #     if self.visualisation:
            #         pipeline = self.obj.get_pipeline()
            #         flags = pipeline.get_property('flags')
            #         pipeline.set_property('flags', flags | 0x00000008)


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
        self.server.send_event('widget_call', self.wid, 'finished')

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
        if not self.pipeline:
            return
        if type == SEEK_PERCENTAGE:
            pos = value / 100.0
        else:
            if not self.obj.get_duration():
                return
            if type == SEEK_RELATIVE:
                pos = self.obj.get_progress() + (1.0 / self.obj.get_duration()) * value
            if type == SEEK_ABSOLUTE:
                pos = (1.0 / self.obj.get_duration()) * value
        self.obj.set_progress(min(pos, 1.0))

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

    #
    # events from gstreamer
    #

    def event_progress(self):
        """
        Progress update
        """
        if not self.pipeline:
            return False
        if self.state in (gst.State.PLAYING, gst.State.PAUSED):
            pos = float(self.pipeline.query_position(gst.Format.TIME)[2]) / 1000000000
            self.server.send_event('widget_call', self.wid, 'progress', pos)
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
            s = caps.get_negotiated_caps().get_structure(0)
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
        self.do_stop()

# initialize gstreamer
ClutterGst.init([])
