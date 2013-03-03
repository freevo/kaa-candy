# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# rectangle.py - rectangle widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# FIXME: instead of using cairo cogl may be faster. But calling
# get_cogl_texture from a Texture does not work for some strange
# reason. This should be fixed here in the future.
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2012-2013 Dirk Meyer
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

# kaa.candy imports
import image

class Rectangle(image.CairoTexture):

    def draw(self, cr):
        """
        Render the cairo context
        """
        stroke = self.border_size or 1
        width = self.width - 2 * stroke
        height = self.height - 2 * stroke
        radius = min(self.radius, width, height)
        x0 = stroke
        y0 = stroke
        x1 = int(x0 + width)
        y1 = int(y0 + height)
        if self.color:
            cr.set_source_rgba(*self.color.to_cairo())
            cr.set_line_width(stroke)
            cr.move_to  (x0, y0 + radius)
            cr.curve_to (x0, y0, x0 , y0, x0 + radius, y0)
            cr.line_to (x1 - radius, y0)
            cr.curve_to (x1, y0, x1, y0, x1, y0 + radius)
            cr.line_to (x1 , y1 - radius)
            cr.curve_to (x1, y1, x1, y1, x1 - radius, y1)
            cr.line_to (x0 + radius, y1)
            cr.curve_to (x0, y1, x0, y1, x0, y1- radius)
            cr.close_path()
            cr.fill()
        if self.border_size and self.border_color:
            cr.set_source_rgba(*self.border_color.to_cairo())
            cr.set_line_width(stroke)
            cr.move_to  (x0, y0 + radius)
            cr.curve_to (x0 , y0, x0 , y0, x0 + radius, y0)
            cr.line_to (x1 - radius, y0)
            cr.curve_to (x1, y0, x1, y0, x1, y0 + radius)
            cr.line_to (x1 , y1 - radius)
            cr.curve_to (x1, y1, x1, y1, x1 - radius, y1)
            cr.line_to (x0 + radius, y1)
            cr.curve_to (x0, y1, x0, y1, x0, y1- radius)
            cr.close_path()
            cr.stroke()
        return True
