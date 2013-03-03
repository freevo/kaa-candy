# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text widget
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
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

__all__ = [ 'Text' ]

from gi.repository import Pango, PangoCairo

import image

class Text(image.CairoTexture):

    def draw(self, cr):
        """
        Render the cairo context
        """
        if self.color:
            cr.set_source_rgba(*self.color.to_cairo())
        layout = PangoCairo.create_layout(cr)
        layout.set_width(self.width * Pango.SCALE)
        layout.set_height(self.height * Pango.SCALE)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_alignment(getattr(Pango.Alignment, str(self.align).upper()))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_font_description(self.font.get_font_description())
        layout.set_text(self.text, -1)
        PangoCairo.show_layout(cr, layout)
