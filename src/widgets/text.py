# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text widget
# -----------------------------------------------------------------------------
# $Id: $
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

import re

import widget
from ..core import Color, Font

class Text(widget.Widget):
    candyxml_name = 'text'
    candy_backend = 'candy.Text'
    attributes = [ 'color', 'font', 'text', 'align' ]
    context_sensitive = True

    def __init__(self, pos, size, text, font, color, align=None, context=None):
        """
        Create Text widget. Unlike a Label a Text widget supports multi-line
        text and markup. See the pango markup documentation.

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget
        @param text: text to show
        @param color: kaa.candy.Color to fill the text
        @param align: align value
        @param context: the context the widget is created in
        """
        super(Text, self).__init__(pos, size, context)
        self.align = align or widget.Widget.ALIGN_LEFT
        self.font = font
        self.text = text
        self.color = color

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the XML element for parameter to create the widget.
        """
        return super(Text, cls).candyxml_parse(element).update(
            text=element.content, align=element.align, color=element.color,
            font=element.font)
