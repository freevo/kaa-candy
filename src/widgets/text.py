# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - multiline text widget
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
#
# First Version: Dirk Meyer <https://github.com/Dischi>
# Maintainer:    Dirk Meyer <https://github.com/Dischi>
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

import re
import kaa.base

import cairo

from gi.repository import Pango, PangoCairo

from widget import Widget
from ..core import Color, Font, create_cairo_context


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

    __text_regexp = re.compile('\$([a-zA-Z][a-zA-Z0-9_\.]*)|\${([^}]*)}')
    __text = None

    def __init__(self, pos, size, text, font, color, align=None, condition=None, context=None):
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
        self._condition = condition
        self.align = align or Widget.ALIGN_LEFT
        self.font = font
        self.text = text
        self.color = color

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, text):
        self.__text_provided = text
        def replace_context(matchobj):
            match = matchobj.groups()[0] or matchobj.groups()[1]
            s = self.context.get(match, '')
            if s is not None:
                return kaa.base.py3_str(s, coerce=True)
            return ''
        if self.context:
            # we have a context, use it
            if self._condition and not self.context.get(self._condition):
                text = ' '      # why does '' not work on update?
            text = re.sub(self.__text_regexp, replace_context, text)
        if self.__text == text:
            return
        self.__text = text
        self.queue_rendering()

    def sync_context(self):
        """
        Adjust to a new context
        """
        self.text = self.__text_provided

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
        cr = create_cairo_context()
        layout = PangoCairo.create_layout(cr)
        layout.set_width(width * Pango.SCALE)
        layout.set_height(height * Pango.SCALE)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_font_description(self.font.get_font_description())
        layout.set_text(self.text, -1)
        PangoCairo.show_layout(cr, layout)
        self.__intrinsic_size_cache = \
            int(min(width, Pango.units_to_double(layout.get_size()[0]))), \
            int(min(height, Pango.units_to_double(layout.get_size()[1])))
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
            font=element.font, condition=element.condition)
