# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# group.py - group widget containing other widgets
# -----------------------------------------------------------------------------
# $Id:$
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
