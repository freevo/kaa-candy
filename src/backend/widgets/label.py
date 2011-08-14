# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# label.py - label widget
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

__all__ = [ 'Label' ]

import cairo
import image

import clutter
import core

class Label(image.CairoTexture):

    def update(self, modified):
        """
        Render the widget
        """
        super(Label, self).update(modified)
        fade = self.font.get_width(self.text) > self.width
        # draw new text string
        context = self.obj.cairo_create()
        context.set_operator(cairo.OPERATOR_SOURCE)
        if self.color:
            context.set_source_rgba(*self.color.to_cairo())
        context.select_font_face(self.font.name, cairo.FONT_SLANT_NORMAL)
        context.set_font_size(self.font.size)
        if fade and self.color:
            s = cairo.LinearGradient(0, 0, self.width, 0)
            c = self.color.to_cairo()
            s.add_color_stop_rgba(0, *c)
            # 50 pixel fading
            s.add_color_stop_rgba(1 - (50.0 / self.width), *c)
            s.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
            context.set_source(s)
        context.move_to(0, context.font_extents()[0])
        context.show_text(self.text)
