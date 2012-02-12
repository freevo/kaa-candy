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

import clutter

class Stage(object):

    def create(self):
        """
        Create the clutter stage object
        """
        self.obj = clutter.Stage()
        self.obj.connect('key-press-event', self.handle_key)
        self.obj.hide_cursor()
        self.keysyms = {}
        # get list of clutter key code. We must access the module
        # first before it is working, therefor we access Left.
        clutter.keysyms.Left
        for name in dir(clutter.keysyms):
            if len(name) == 2 and name.startswith('_'):
                self.keysyms[getattr(clutter.keysyms, name)] = name[1]
            if not name.startswith('_'):
                self.keysyms[getattr(clutter.keysyms, name)] = name
    
    def handle_key(self, stage, event):
        """
        Translate clutter keycode to name and emit signal in main loop. This
        function is a callback from clutter.
        """
        key = self.keysyms.get(event.keyval) or event.keyval
        self.server.send_event('key-press', key)

    def ensure_redraw(self):
        self.obj.ensure_redraw()

    def init(self, size):
        """
        Set the size and the base group
        """
        self.obj.set_size(*size)
        self.obj.set_color(clutter.Color(0, 0, 0, 0xff))
        self.obj.show()
