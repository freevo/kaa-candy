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

__all__ = [ 'Video', 'Audio', 'SEEK_RELATIVE', 'SEEK_ABSOLUTE', 'SEEK_PERCENTAGE',
            'STATE_IDLE', 'STATE_PLAYING', 'STATE_PAUSED', 'NEXT', 'POSSIBLE_PLAYER' ]

# python imports
import logging

# kaa imports
import kaa
import kaa.metadata

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

ASPECT_ORIGINAL = 'ASPECT_ORIGINAL'
ASPECT_16_9 = 'ASPECT_16_9'
ASPECT_4_3 = 'ASPECT_4_3'
ASPECT_ZOOM = 'ASPECT_ZOOM'

ASPECTS = [ ASPECT_ORIGINAL, ASPECT_16_9, ASPECT_4_3, ASPECT_ZOOM ]

NEXT = 'NEXT'

# filled with values from the backend later
POSSIBLE_PLAYER = []

class Video(Widget):
    """
    Video widget
    """
    candyxml_name = 'video'
    candy_backend = 'candy.Video'

    attributes = [ 'uri', 'config', 'audio_only', 'player' ]
    audio_only = False

    __player = None

    def __init__(self, pos=None, size=None, uri=None, player='gstreamer', context=None):
        """
        Create the video widget. The widget supports gstreamer
        (default) and mplayer but only gstreamer can be used as real
        widget for now. When choosing mplayer it will always open a
        full screen window to play the video.

        The playback can be configured using the config member
        dictionary. Please note, that gstreamer tries to figure out
        most of the stuff itself and AC3 and DTS passthrough only
        works when using pulseaudio and pulseaudio configured
        correctly (pavucontrol). Future versions of kaa.candy may have
        more or changed options.
        """
        super(Video, self).__init__(pos, size, context)
        self.uri = uri
        self.signals = kaa.Signals('finished', 'progress', 'streaminfo')
        self.state = STATE_IDLE
        # player configuration
        self.config = {
            'mplayer.vdpau': False,
            'mplayer.passthrough': False,
            'fresh-rate': None
        }
        # current streaminfo / audio / subtitle values
        self.streaminfo = {
            'audio': {},
            'subtitle': {},
            'is_menu': False,
        }
        self.aid = 0
        self.sid = -1
        self.aspect = ASPECT_ORIGINAL
        self.player = player or 'gstreamer'

    @property
    def player(self):
        return self.__player

    @player.setter
    def player(self, value):
        if self.state != STATE_IDLE:
            raise RuntimeError('player already running')
        self.__player = value

    @property
    def uri(self):
        return self.__uri

    @uri.setter
    def uri(self, value):
        if value and isinstance(value, (str, unicode)) and value.startswith('$'):
            # variable from the context, e.g. $varname
            value = self.context.get(value) or ''
        if value and not value.find('://') > 0:
            value = 'file://' + value
        if value:
            self.metadata = kaa.metadata.parse(value)
        else:
            self.metadata = None
        self.__uri = value

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget.
        """
        return super(Video, cls).candyxml_parse(element).update(
            uri=element.uri or element.filename, player=element.player)

    #
    # public API to control the player
    #

    def play(self):
        """
        Start the playback
        """
        if self.state != STATE_IDLE:
            raise RuntimeError('player already running')
        if self.player not in POSSIBLE_PLAYER:
            raise RuntimeError('unknown player %s' % self.player)
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
        if idx == NEXT:
            if not self.streaminfo or not self.streaminfo['audio']:
                return 0
            aid = self.streaminfo['audio'].keys()
            aid.sort()
            if not self.aid in aid:
                idx = 0
            else:
                idx = aid.index(self.aid) + 1
                if idx >= len(aid):
                    idx = 0
            idx = aid[idx]
        self.backend.do_set_audio(idx)
        self.aid = idx
        return idx

    def set_subtitle(self, idx):
        """
        Set the subtitle sream idx. Use -1 to turn subtitles off.
        """
        if idx == NEXT:
            if not self.streaminfo or not self.streaminfo['subtitle']:
                return -1
            sid = self.streaminfo['subtitle'].keys()
            sid.sort()
            if not self.sid in sid:
                idx = sid[0]
            else:
                idx = sid.index(self.sid) + 1
                if idx >= len(sid):
                    idx = -1
                else:
                    idx = sid[idx]
        self.backend.do_set_subtitle(idx)
        self.sid = idx
        return idx

    def set_deinterlace(self, value):
        """
        Turn on/off deinterlacing
        """
        self.backend.do_set_deinterlace(value)

    def set_aspect(self, aspect):
        """
        Set the aspect ratio
        """
        if aspect == NEXT:
            aspect = ASPECTS[(ASPECTS.index(self.aspect) + 1) % len(ASPECTS)]
        self.backend.do_set_aspect(aspect)
        self.aspect = aspect

    def nav_command(self, cmd):
        """
        Send DVD navigation command
        """
        self.backend.do_nav_command(cmd)

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
        self.state = STATE_IDLE
        self.signals['finished'].emit()

    def event_streaminfo(self, streaminfo):
        """
        Callback from the backend: streaminfo
        """
        del streaminfo['sync']
        self.signals['streaminfo'].emit(streaminfo)
        self.streaminfo = streaminfo

class Audio(Video):
    """
    Hidden video widget for audio only
    """
    candyxml_name = 'audio'
    candy_backend = 'candy.Audio'
    audio_only = True

    attributes = Video.attributes + [ 'visualisation' ]

    def __init__(self, pos=None, size=None, uri=None, player='gstreamer', visualisation=None,
                 context=None):
        """
        Create the audio widget. If visualisation is None it is invisible.
        """
        super(Audio, self).__init__(pos, size, uri, player, context)
        self.visualisation = visualisation

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget.
        """
        return super(Audio, cls).candyxml_parse(element).update(
            visualisation=element.visualisation)
