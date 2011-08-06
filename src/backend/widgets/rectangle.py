# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# rectangle.py - rectangle widget
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

__all__ = [ 'Rectangle' ]

import image

clutter = candy_module('clutter')

class Rectangle(image.CairoTexture):

    def update(self, modified):
        """
        Render the widget
        """
        super(Rectangle, self).update(modified)
        context = self.obj.cairo_create()
        stroke = self.border_size or 1
        width = self.width - 2 * stroke
        height = self.height - 2 * stroke
        radius = min(self.radius, width, height)
        x0 = stroke
        y0 = stroke
        x1 = int(x0 + width)
        y1 = int(y0 + height)
        if self.color:
            context.set_source_rgba(*self.color.to_cairo())
            context.set_line_width(stroke)
            context.move_to  (x0, y0 + radius)
            context.curve_to (x0, y0, x0 , y0, x0 + radius, y0)
            context.line_to (x1 - radius, y0)
            context.curve_to (x1, y0, x1, y0, x1, y0 + radius)
            context.line_to (x1 , y1 - radius)
            context.curve_to (x1, y1, x1, y1, x1 - radius, y1)
            context.line_to (x0 + radius, y1)
            context.curve_to (x0, y1, x0, y1, x0, y1- radius)
            context.close_path()
            context.fill()
        if self.border_size and self.border_color:
            context.set_source_rgba(*self.border_color.to_cairo())
            context.set_line_width(stroke)
            context.move_to  (x0, y0 + radius)
            context.curve_to (x0 , y0, x0 , y0, x0 + radius, y0)
            context.line_to (x1 - radius, y0)
            context.curve_to (x1, y0, x1, y0, x1, y0 + radius)
            context.line_to (x1 , y1 - radius)
            context.curve_to (x1, y1, x1, y1, x1 - radius, y1)
            context.line_to (x0 + radius, y1)
            context.curve_to (x0, y1, x0, y1, x0, y1- radius)
            context.close_path()
            context.stroke()
        del context
