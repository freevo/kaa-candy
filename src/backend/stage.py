# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# stage - Backend stage class
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2012 Dirk Meyer
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

    def set_active(self, state):
        """
        Set the stage active or inactive
        """
        # set_opacity does not work on the state
        for child in self.obj.get_children():
            child.save_easing_state()
            child.set_easing_duration(200)
            factor = 2.0 if state else 1/2.0
            child.set_opacity(child.get_opacity() * factor)
            child.restore_easing_state()

    def handle_key(self, stage, event):
        """
        Translate clutter keycode to name and emit signal in main loop. This
        function is a callback from clutter.
        """
        for key in self.keysyms.get(event.keyval, []):
            self.server.send_event('key-press', key)

    def ensure_redraw(self):
        self.obj.ensure_redraw()

    def init(self, size, fullscreen):
        """
        Set the size and the base group
        """
        self.obj.set_size(*size)
        if fullscreen:
            self.obj.set_fullscreen(True)
        self.obj.set_color(clutter.Color.new(0, 0, 0, 0xff))
        self.obj.show()
