# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# label.py - label widget
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

__all__ = [ 'Label' ]

import re

import widget
from ..core import Color, Font

class Label(widget.Widget):
    candyxml_name = 'label'
    candy_backend = 'candy.Label'
    attributes = [ 'color', 'font', 'text' ]
    context_sensitive = True

    __text_regexp = re.compile('\$([a-zA-Z][a-zA-Z0-9_\.]*)|\${([^}]*)}')

    def __init__(self, pos=None, size=None, color=None, font=None, text='', context=None):
        """
        Create a new label widget

        @param pos: (x,y) position of the widget or None
        @param text: Text to render. This can also be a context based string like
            C{$text} with the context containing C{text='My String'}. This will
            make the widget context sensitive.
        @param size: (width,height) geometry of the widget.
        @param font: kaa.candy.Font object
        @param context: the context the widget is created in
        """
        super(Label, self).__init__(pos, size, context)
        self.color = color
        self.font = font
        self.text = text

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
                return unicode(s)
            return ''
        if self.context:
            # we have a context, use it
            text = re.sub(self.__text_regexp, replace_context, text)
        self.__text = text
        self.queue_rendering()

    def context_sync(self):
        self.text = self.__text_provided

    def calculate_intrinsic_size(self, size):
        """
        Calculate intrinsic size based on the parent's size
        """
        super(Label, self).calculate_intrinsic_size(size)
        if self.font.size == 0:
            # FIXME: wrong when the widget size changes
            self.font = self.font.get_font(self.height)
        width, height = self.font.get_width(self.text), self.font.get_height(Font.MAX_HEIGHT)
        if self.width and width > self.width and self.width > 0:
            width = self.width
        self.intrinsic_size = width, height
        return width, height

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <label y='50' width='100' font='Vera:24' color='0xffffffff'>
              text to show
          </label>
        The text can also be a context based variable like C{$text}. This
        will make the widget context sensitive.
        """
        return super(Label, cls).candyxml_parse(element).update(
            font=element.font, color=element.color, text=element.content)
