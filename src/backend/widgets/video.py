# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# vieo.py - video widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
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

__all__ = [ 'Video' ]

from gi.repository import Clutter as clutter

import kaa.metadata

import group

import gstreamer
import mplayer

player = {
    'gstreamer': gstreamer.Gstreamer,
    'mplayer': mplayer.Mplayer
}

class Video(group.Group):

    player_obj = None
    old_player = None

    attributes = [ 'width', 'height', 'uri', 'config', 'audio_only', 'player' ]

    def create(self):
        super(Video, self).create()
        self.delayed = []

    def prepare(self, modified):
        """
        Prepare rendering
        """
        if 'player' in modified and self.player:
            if self.player_obj:
                self.old_player = self.player_obj.obj
            self.player_obj = player[self.player]()
            self.player_obj.x = self.player_obj.y = 0
            self.player_obj.wid = self.wid
            self.player_obj.server = self.server
        for a in self.attributes:
            setattr(self.player_obj, a, getattr(self, a))
        self.player_obj.prepare(modified)

    def update(self, modified):
        """
        Render the widget
        """
        super(Video, self).update(modified)
        if self.old_player:
            print 'del old'
            self.obj.remove_actor(self.old_player)
            self.old_player = None
        if 'width' in modified or 'height' in modified:
            self.obj.set_clip(0, 0, self.width, self.height)
        if 'uri' in modified and self.uri:
            self.streaminfo = {
                'audio': {},
                'subtitle': {},
                'is_menu': False,
                'sync': True
            }
            metadata = kaa.metadata.parse(self.uri)
            if metadata and 'audio' in metadata:
                # video item, not audio only
                for audio in metadata.audio:
                    self.streaminfo['audio'][audio.id] = None if audio.langcode == 'und' else audio.langcode
                for sub in metadata.subtitles:
                    self.streaminfo['subtitle'][sub.id] = None if sub.langcode == 'und' else sub.langcode
            self.send_widget_event('streaminfo', self.streaminfo)
        if 'player' in modified and self.player:
            self.player_obj.create()
            self.obj.add_actor(self.player_obj.obj)
            self.player_obj.update(modified)

    #
    # control callbacks from the main process
    #

    def __getattr__(self, attr):
        return getattr(self.player_obj, attr)
