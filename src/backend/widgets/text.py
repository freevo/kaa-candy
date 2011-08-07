# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text widget
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

__all__ = [ 'Text' ]

import cairo
import widget

clutter = candy_module('clutter')
core = candy_module('core')

class Text(widget.Widget):

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.CairoTexture(*self.calculate_size()[:2])
        self.obj.show()

    def calculate_size(self):
        fade = False
        if self.font.size == 0:
            # get font based on widget height
            self.font = self.font.get_font(self.height)
        # get widget width and height
        width = self.font.get_width(self.text)
        height = self.font.get_height(core.Font.MAX_HEIGHT)
        if self.width and width > self.width:
            fade = True
            width = self.width
        return int(width), int(height), fade

    def update(self, modified):
        """
        Render the widget
        """
        super(Text, self).update(modified)
        width, height, fade = self.calculate_size()
        if width != self.obj.get_width() or height != self.obj.get_height():
            self.obj.set_surface_size(int(width), int(height))
        self.obj.clear()
        # draw new text string
        context = self.obj.cairo_create()
        context.set_operator(cairo.OPERATOR_SOURCE)
        if self.color:
            context.set_source_rgba(*self.color.to_cairo())
        context.select_font_face(self.font.name, cairo.FONT_SLANT_NORMAL)
        context.set_font_size(self.font.size)
        if fade and self.color:
            s = cairo.LinearGradient(0, 0, width, 0)
            c = self.color.to_cairo()
            s.add_color_stop_rgba(0, *c)
            # 50 pixel fading
            s.add_color_stop_rgba(1 - (50.0 / width), *c)
            s.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
            context.set_source(s)
        context.move_to(0, context.font_extents()[0])
        context.show_text(self.text)
