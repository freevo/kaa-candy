# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# label.py - label widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2013 Dirk Meyer
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

__all__ = [ 'Label' ]

# cairo imports
import cairo

# kaa.candy imports
import image
import core

class Label(image.CairoTexture):

    def draw(self, cr):
        """
        Render the cairo context
        """
        fade = self.font.get_width(self.text) > self.width
        # draw new text string
        if self.color:
            cr.set_source_rgba(*self.color.to_cairo())
        cr.select_font_face(self.font.name, cairo.FONT_SLANT_NORMAL)
        cr.set_font_size(self.font.size)
        if fade and self.color:
            s = cairo.LinearGradient(0, 0, self.width, 0)
            c = self.color.to_cairo()
            s.add_color_stop_rgba(0, *c)
            # 50 pixel fading
            s.add_color_stop_rgba(1 - (50.0 / self.width), *c)
            s.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
            cr.set_source(s)
        cr.move_to(0, cr.font_extents()[0])
        cr.show_text(self.text)
        return True
