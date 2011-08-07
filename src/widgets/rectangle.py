# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# rectangle.py - Rectangle Widget
# -----------------------------------------------------------------------------
# $Id: rectangle.py 3763 2009-01-10 19:56:30Z dmeyer $
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

__all__ = [ 'Rectangle' ]

import widget
from ..core import Color

class Rectangle(widget.Widget):
    candyxml_name = 'rectangle'
    candy_backend = 'candy.Rectangle'
    attributes = [ 'color', 'border_size', 'border_color', 'radius' ]

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
