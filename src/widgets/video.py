# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# video.py - video widget
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

__all__ = [ 'Video', 'SEEK_RELATIVE', 'SEEK_ABSOLUTE', 'SEEK_PERCENTAGE',
            'STATE_IDLE', 'STATE_PLAYING', 'STATE_PAUSED' ]

# python imports
import logging

# kaa imports
import kaa

# kaa.candy imports
from widget import Widget
from .. import config

# get logging object
log = logging.getLogger('kaa.candy')

SEEK_RELATIVE = 'SEEK_RELATIVE'
SEEK_ABSOLUTE = 'SEEK_ABSOLUTE'
SEEK_PERCENTAGE = 'SEEK_PERCENTAGE'

STATE_IDLE = 'STATE_IDLE'
STATE_PLAYING = 'STATE_PLAYING'
STATE_PAUSED = 'STATE_PAUSED'

class Video(Widget):
    """
    Video widget
    """
    candyxml_name = 'video'

    attributes = [ 'url', 'config' ]

    def __init__(self, pos=None, size=None, url=None, player='gstreamer', context=None):
        """
        Create the video widget. The widget supports gstreamer
        (default) and mplayer but only gstreamer can be used as real
        widget for now. When choosing mplayer it will always open a
        full screen window to play the video.

        This it is not possible to set as argument the player when
        using CandyXML without defining it in the XML file a special
        variable 'candy_player' in the context can be used.

        The playback can be configured using the config member
        dictionary. Please note, that gstreamer tries to figure out
        most of the stuff itself and AC3 and DTS passthrough only
        works when using pulseaudio and pulseaudio configured
        correctly (pavucontrol). Future versions of kaa.candy may have
        more or changed options.
        """
        super(Video, self).__init__(pos, size, context)
        if url and isinstance(url, (str, unicode)) and url.startswith('$'):
            # variable from the context, e.g. $varname
            url = self.context.get(url) or ''
        self.url = url
        self.signals = kaa.Signals('finished', 'progress')
        self.state = STATE_IDLE
        # player configuration
        self.config = {
            'mplayer.vdpau': False,
            'mplayer.passthrough': False,
        }
        if not player:
            player = self.context.get('candy_player')
        self.set_player(player)

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget.
        """
        return super(Video, cls).candyxml_parse(element).update(
            url=element.url or element.filename, player=element.player)

    #
    # public API to control the player
    #

    def set_player(self, player):
        """
        Set the player. This can be done until the widget is bound to
        a stage by adding it to a parent.
        """
        if self.stage:
            raise RuntimeError('backend widget already created')
        if player == 'gstreamer' or player == None:
            self.candy_backend = 'candy.Gstreamer'
        elif player == 'mplayer':
            self.candy_backend = 'candy.Mplayer'
        else:
            raise AttributeError('unsuported player %s' % player)

    def play(self):
        """
        Start the playback
        """
        if self.state != STATE_IDLE:
            raise RuntimeError('player already running')
        self.state = STATE_PLAYING
        self.backend.do_play()

    def stop(self):
        """
        Stop the playback
        """
        if self.state != STATE_IDLE:
            self.backend.do_stop()

    def pause(self):
        """
        Pause playback
        """
        if self.state == STATE_PLAYING:
            self.backend.do_pause()
            self.state = STATE_PAUSED

    def resume(self):
        """
        Resume a paused playback
        """
        if self.state == STATE_PAUSED:
            self.backend.do_resume()
            self.state = STATE_PLAYING

    def seek(self, value, type=SEEK_RELATIVE):
        """
        Seek to the given position. Type is either SEEK_RELATIVE
        (default), SEEK_ABSOLUTE or SEEK_PERCENTAGE.
        """
        self.backend.do_seek(value, type)

    def set_audio(self, idx):
        """
        Set the audio channel to stream number idx
        """
        self.backend.do_set_audio(idx)

    #
    # backend callbacks
    #

    def event_progress(self, pos):
        """
        Callback from the backend: new progress information
        """
        self.signals['progress'].emit(pos)

    def event_finished(self):
        """
        Callback from the backend: playback finished
        """
        self.signals['finished'].emit()
