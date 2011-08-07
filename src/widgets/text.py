# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# text.py - text Widget
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

import widget
from ..core import Color, Font

class Text(widget.Widget):
    candyxml_name = 'text'
    candy_backend = 'candy.Text'
    attributes = widget.Widget.attributes + [ 'color', 'font', 'text' ]

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
        super(Text, self).__init__(pos, size, context)
        self.color = color
        self.font = font
        self.text = text

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <text y='50' width='100' font='Vera:24' color='0xffffffff'>
              text to show
          </text>
        The text can also be a context based variable like C{$text}. This
        will make the widget context sensitive.
        """
        return super(Text, cls).candyxml_parse(element).update(
            font=element.font, color=element.color, text=element.content)
