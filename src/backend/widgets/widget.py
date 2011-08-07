# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# widget.py - base widgets class
# -----------------------------------------------------------------------------
# $Id:$
#
# This file contains the clutter code executed in the rendering
# process and not the process importing kaa.candy.
#
# -----------------------------------------------------------------------------
# kaa-candy - Third generation Canvas System using Clutter as backend
# Copyright (C) 2008-2011 Dirk Meyer, Jason Tackaberry
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file AUTHORS for a complete list of authors.
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

__all__ = [ 'Widget' ]

class Widget(object):

    # clutter object
    obj = None
    # candy parent object
    parent = None

    ALIGN_LEFT = 'left'
    ALIGN_RIGHT = 'right'
    ALIGN_TOP = 'top'
    ALIGN_BOTTOM = 'bottom'
    ALIGN_CENTER = 'center'
    ALIGN_SHRINK = 'shrink'

    def prepare(self, modified):
        """
        Prepare rendering
        Executed in the kaa mainloop
        """
        pass

    def create(self):
        """
        Create the clutter object
        Executed in the clutter thread
        """
        pass

    def delete(self):
        """
        Delete the clutter object
        Executed in the clutter thread
        """
        if not self.obj:
            return
        if self.parent and self.parent.obj:
            self.parent.obj.remove(self.obj)
        self.obj = None

    def reparent(self, parent):
        """
        Reparent the clutter object
        Executed in the clutter thread
        """
        if self.parent:
            self.parent.obj.remove(self.obj)
        self.parent = parent
        if self.parent:
            self.parent.obj.add(self.obj)

    def update(self, modified):
        """
        Render the widget
        Executed in the clutter thread
        """
        if 'x' in modified or 'y' in modified:
            self.obj.set_position(self.x, self.y)
        if 'width' in modified and self.width:
            self.obj.set_width(self.width)
        if 'height' in modified and self.height:
            self.obj.set_height(self.height)
