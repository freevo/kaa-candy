# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# label.py - label widget
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

__all__ = [ 'Label' ]

import image

import cairo
from gi.repository import Clutter as clutter

import core

class Label(image.CairoTexture):
    
    def draw(self, texture, cr):
        """
        Render the widget
        """
        super(Label, self).draw(texture, cr)
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
