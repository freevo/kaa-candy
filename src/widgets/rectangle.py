# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# rectangle.py - rectangle widget
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
#
# First Version: Dirk Meyer <https://github.com/Dischi>
# Maintainer:    Dirk Meyer <https://github.com/Dischi>
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

__all__ = [ 'Rectangle' ]

from widget import Widget
from ..core import Color

class Rectangle(Widget):
    candyxml_name = 'rectangle'
    candy_backend = 'candy.Rectangle'
    attributes = [ 'color', 'border_size', 'border_color', 'radius' ]

    attribute_types = {
        'color': Color,
        'border_color': Color
    }

    def __init__(self, pos=None, size=None, color=None, border_size=0,
                 border_color=None, radius=0, context=None):
        """
        Create a Rectangle widget

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget.
        @param color: kaa.candy.Color to fill the rectangle
        @param border_size: size of the rectangle border
        @param border_color: kaa.candy.Color of the border. This argument is
            not needed when border_size is 0.
        @param radius: radius for a rectangle with round edges.
        """
        super(Rectangle, self).__init__(pos, size, context)
        self.color = color
        self.border_size = border_size
        self.border_color = border_color
        self.radius = radius

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
            <rectangle x='0' y='0' width='100' height='100' color='0xff0000'
                border_size='2' border_color='0x000000' radius='10'/>
        """
        return super(Rectangle, cls).candyxml_parse(element).update(
            radius=int(element.radius or 0), border_size=int(element.border_size or 0),
            color=element.color, border_color=element.border_color)
