# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# widget.py - base widgets class
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

__all__ = [ 'Widget' ]

from gi.repository import Clutter as clutter

class Widget(object):

    # clutter object
    obj = None

    # internal id of the widget on client and server
    wid = None

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

    def send_widget_event(self, *args):
        """
        Send an event to the candy widget
        """
        self.server.send_event('widget_call', self.wid, *args)
        
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
            self.obj.get_parent().remove_actor(self.obj)
        self.obj = None

    def reparent(self, parent, sibling):
        """
        Reparent the clutter object
        Executed in the clutter thread
        """
        if self.obj.get_parent():
            self.obj.get_parent().remove_actor(self.obj)
        if parent and sibling and sibling.obj.get_parent():
            parent.obj.insert_child_above(self.obj, sibling.obj)
        elif parent and sibling:
            print 'oops', sibling.wid
            parent.obj.add_actor(self.obj)
        elif parent:
            parent.obj.add_actor(self.obj)

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

    def above_sibling(self, sibling):
        """
        Move the widget above the given sibling
        """
        self.obj.get_parent().set_child_above_sibling(self.obj, sibling.obj)

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
        if 'scale_x' in modified or 'scale_y' in modified:
            self.obj.set_scale(self.scale_x, self.scale_y)
        if 'anchor_point' in modified:
            self.obj.set_anchor_point(*self.anchor_point)
        if 'visible' in modified:
            if self.visible:
                self.obj.show()
            else:
                self.obj.hide()

    def animate(self, ease, secs, *args):
        # Note: it is not possible to stop or modify an animation
        # right now. The result from this call has to go back to the
        # main app somehow.
        keys = []
        values = []
        args = list(args)
        while args:
            keys.append(args.pop(0))
            values.append(args.pop(0))
        self.obj.animatev(getattr(clutter.AnimationMode, ease), int(secs * 1000) or 1, keys, values)
