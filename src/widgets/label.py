# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# label.py - text label widget
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

# python
import re
import kaa.base

# kaa.candy imports
from widget import Widget
from ..core import Color, Font

class Label(Widget):
    """
    Text label widget
    """
    candyxml_name = 'label'
    candy_backend = 'candy.Label'
    attributes = [ 'color', 'font', 'text' ]
    attribute_types = {
        'color': Color,
        'font': Font
    }

    __text_regexp = re.compile('\$([a-zA-Z][a-zA-Z0-9_\.]*)|\${([^}]*)}')
    __text = None

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
                return kaa.base.py3_str(s, coerce=True)
            return ''
        if self.context:
            # we have a context, use it
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
        super(Label, self).sync_layout(size)
        if self.font.size == 0:
            # FIXME: wrong when the widget size changes
            self.font = self.font.get_font(self.height)
        width, height = self.font.get_width(self.text), self.font.get_height(Font.MAX_HEIGHT)
        if self.width and width > self.width and self.width > 0:
            width = self.width
        self.intrinsic_size = width, height

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
