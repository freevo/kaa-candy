# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# group.py - group widget containing other widgets
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

__all__ = [ 'Group' ]

from gi.repository import Clutter as clutter

import widget

class Group(widget.Widget):

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.Group.new()
        self.obj.show()

    def hide(self):
        """
        Hide the widget
        """
        self.obj.hide()

    def show(self):
        """
        Show the widget
        """
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        super(Group, self).update(modified)
        if 'clip' in modified:
            if self.clip:
                (x, y), (width, height) = self.clip
                self.obj.set_clip(x, y, width, height)
            else:
                self.obj.remove_clip()
