# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# widget.py - base widgets class
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

__all__ = [ 'Widget' ]

import clutter

class Widget(object):

    # clutter object
    obj = None

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
        if self.obj and self.obj.get_parent():
            self.obj.get_parent().remove(self.obj)
        self.obj = None

    def reparent(self, parent):
        """
        Reparent the clutter object
        Executed in the clutter thread
        """
        if self.obj.get_parent():
            self.obj.get_parent().remove(self.obj)
        if parent:
            parent.obj.add(self.obj)

    def set_position(self):
        """
        Set a new position without re-rendering the widget
        Executed in the clutter thread
        """
        self.obj.set_position(self.x, self.y)

    def raise_top(self):
        """
        Raise widget to the top of the stack
        """
        self.obj.raise_top()

    def lower_bottom(self):
        """
        Lower widget to the bottom of the stack
        """
        self.obj.lower_bottom()

    def update(self, modified):
        """
        Render the widget
        Executed in the clutter thread
        """
        if 'width' in modified and self.width:
            self.obj.set_width(self.width)
        if 'height' in modified and self.height:
            self.obj.set_height(self.height)
        if 'opacity' in modified:
            self.obj.set_opacity(self.opacity)
        if 'scale' in modified:
            self.obj.set_scale(*self.scale)
        if 'anchor_point' in modified:
            self.obj.set_anchor_point(*self.anchor_point)

    def animate(self, ease, secs, *args):
        # Note: it is not possible to stop or modify an animation
        # right now. The result from this call has to go back to the
        # main app somehow.
        self.obj.animate(getattr(clutter, ease), int(secs * 1000) or 1, *args)
