# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - multiline text widget
# -----------------------------------------------------------------------------
# $Id:$
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

__all__ = [ 'Text' ]

import re

# we need to import clutter here to calculate the size. Clutter itself
# is never initialized and its main loop is not started. If someone
# knows a better way to get the intrinsic size, please change this.
import pango
import clutter

from widget import Widget
from ..core import Color, Font

class Text(Widget):
    candyxml_name = 'text'
    candy_backend = 'candy.Text'
    attributes = [ 'color', 'font', 'text', 'align' ]
    attribute_types = {
        'color': Color,
        'font': Font
    }

    __intrinsic_size_param = None
    __intrinsic_size_cache = None

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
        self.align = align or Widget.ALIGN_LEFT
        self.font = font
        self.text = text
        self.color = color

    def sync_layout(self, size):
        """
        Sync layout changes and calculate intrinsic size based on the
        parent's size.
        """
        super(Text, self).sync_layout(size)
        width, height = self.size
        if self.__intrinsic_size_param == (width, height, self.text, self.font.name, self.font.size):
            self.intrinsic_size = self.__intrinsic_size_cache
            return self.__intrinsic_size_cache
        # ugly hack: we need clutter to help us get the size we need
        obj = clutter.Text()
        obj.set_size(width, height)
        obj.set_line_wrap(True)
        obj.set_line_wrap_mode(pango.WRAP_WORD_CHAR)
        obj.set_use_markup(True)
        obj.set_font_name("%s %spx" % (self.font.name, self.font.size))
        obj.set_text(self.text)
        self.__intrinsic_size_cache = pango.units_to_double(obj.get_layout().get_size()[0]), \
            pango.units_to_double(obj.get_layout().get_size()[1])
        self.__intrinsic_size_param = (width, height, self.text, self.font.name, self.font.size)
        self.intrinsic_size = self.__intrinsic_size_cache
        return self.__intrinsic_size_cache

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the XML element for parameter to create the widget.
        """
        return super(Text, cls).candyxml_parse(element).update(
            text=element.content, align=element.align, color=element.color,
            font=element.font)
