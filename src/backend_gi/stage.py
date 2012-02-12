# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# stage - Backend stage class
# -----------------------------------------------------------------------------
# $Id: $
#
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
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

from gi.repository import Clutter as clutter

class Stage(object):

    def create(self):
        """
        Create the clutter stage object
        """
        self.obj = clutter.Stage.get_default()
        self.obj.hide_cursor()
        self.obj.connect('key-press-event', self.handle_key)
        self.keysyms = {}
        for name in dir(clutter):
            if name.startswith('KEY_'):
                if not getattr(clutter, name) in self.keysyms:
                    self.keysyms[getattr(clutter, name)] = []
                self.keysyms[getattr(clutter, name)].append(name[4:])

    def handle_key(self, stage, event):
        """
        Translate clutter keycode to name and emit signal in main loop. This
        function is a callback from clutter.
        """
        for key in self.keysyms.get(event.key.keyval, []):
            self.server.send_event('key-press', key)

    def ensure_redraw(self):
        self.obj.ensure_redraw()

    def init(self, size):
        """
        Set the size and the base group
        """
        self.obj.set_size(*size)
        self.obj.set_color(clutter.Color.new(0, 0, 0, 0xff))
        self.obj.show()
