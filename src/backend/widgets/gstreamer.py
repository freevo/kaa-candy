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

__all__ = [ 'Gstreamer' ]

# Python imports
import os
import sys

# Clutter and GStreamer GI bindings
from gi.repository import Clutter as clutter, ClutterGst, Gst as gst

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

class Gstreamer(widget.Widget):
    """
    Gstreamer video widget.
    """

    state = gst.State.NULL

    def create(self):
        """
        Create the clutter object
        """
        self.delayed = []
        self.obj = ClutterGst.VideoTexture()
        self.obj.set_seek_flags(ClutterGst.SeekFlags(1))
        self.obj.connect("notify::progress", self.event_progress)
        self.obj.connect("eos", self.event_finished)
        self.obj.set_keep_aspect_ratio(True)
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
        if 'url' in modified and self.url:
            self.obj.set_filename(self.url)

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
        self.server.send_event('widget_call', self.wid, 'finished')

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
        # Sekk nowhere. This is kind of stupid but clutter-gst does
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

    #
    # events from gstreamer
    #

    def event_progress(self, media, pspec):
        """
        Progress update
        """
        if self.state in (gst.State.PLAYING, gst.State.PAUSED):
            pos = media.get_progress() * media.get_duration()
            self.server.send_event('widget_call', self.wid, 'progress', pos)
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
        self.server.send_event('widget_call', self.wid, 'finished')

# initialize gstreamer
ClutterGst.init(sys.argv)
