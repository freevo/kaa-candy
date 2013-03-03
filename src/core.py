# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - Core classes
# -----------------------------------------------------------------------------
# Note: this file is imported from the application using kaa.candy as
# well as the rendering process. Therefore, no imports from this file
# to other parts of kaa.candy are allowed to avoid strange side
# effects.
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

__all__ = [ 'Context', 'Color', 'Font' ]

# python imports
import logging
import cairo

from gi.repository import Pango

# kaa imports
import kaa

# get logging object
log = logging.getLogger('kaa.candy')

class Context(dict):

    def __init__(self, ctx=None, **kwargs):
        if ctx is not None:
            super(Context, self).__init__(ctx.copy())
        self.update(kwargs)

    def get(self, attr, default=None):
        if attr.startswith('$'):
            # strip prefix for variables if set
            attr = attr[1:]
        try:
            # try the variable as it is
            value = eval(attr, self)
            return value
        except Exception, e:
            log.error('unable to evaluate %s', attr)
            return default

    def __getattr__(self, attr):
        return self.get(attr)


class Color(list):
    """
    Color object which is a list of r,g,b,a with values between 0 and 255.
    """
    def __init__(self, *col):
        """
        Create a new color object. All C{set_color} member functions of kaa.candy
        widgets use this class for setting a color and not the clutter color object.
        The Color object is list of r,g,b,a with values between 0 and 255.

        @param col: one of the following types
         - a tuple r,g,b,a
         - a clutter color object
         - a string #aarrggbb
        """
        if len(col) > 1:
            return super(Color, self).__init__(col)
        col = col[0]
        if col == None:
            return super(Color, self).__init__((0,0,0,255))
        if hasattr(col, 'red'):
            # clutter.Color object
            return super(Color, self).__init__((col.red, col.green, col.blue, col.alpha))
        if isinstance(col, (list, tuple)):
            # tuple as one argument
            return super(Color, self).__init__(col)
        # Convert a 32-bit ARGB string 0xaarrggbb
        if not isinstance(col, (int, long)):
            col = long(col, 16)
        a = 255 - ((col >> 24) & 0xff)
        r = (col >> 16) & 0xff
        g = (col >> 8) & 0xff
        b = (col >> 0) & 0xff
        super(Color, self).__init__((r,g,b,a))

    def to_cairo(self):
        """
        Convert to list used by cairo.

        @returns: list with float values from 0 to 1.0
        """
        return [ x / 255.0 for x in self ]


# helping cairo surface
_font_cairo_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)

def create_cairo_context():
    """
    Create a dummy cairo context object for font calculations.
    """
    return cairo.Context(_font_cairo_surface)


class Font(object):
    """
    Font object containing font name and font size

    @ivar name: font name
    @ivar size: font size
    """

    __height_cache = {}

    ASCENT, TYPICAL, MAX_HEIGHT = range(3)

    def __init__(self, name):
        """
        Create a new font object
        @param name: name and size of the font, e.g. Vera:24
        """
        self.name = name
        self.size = 0
        if name.find(':') > 0:
            self.name, size = name.split(':')
            self.size = int(size)

    def get_height(self, field=None, size=None):
        """
        Get height of a text with this font.
        @returns: ascent (typical height above the baseline), normal (typical height
            of a string without special characters) and ascent + descent
        """
        if size is None:
            size = self.size
        info = self.__height_cache.get((self.name, size))
        if info is None:
            c = create_cairo_context()
            c.select_font_face(self.name, cairo.FONT_SLANT_NORMAL)
            c.set_font_size(size)
            ascent, descent = c.font_extents()[:2]
            info = int(ascent), int(-c.text_extents(u'Ag')[1]), int(ascent + descent)
            self.__height_cache[(self.name, size)] = info
        if field is None:
            return info
        return info[field]

    def get_width(self, text):
        """
        Get width of the given string
        """
        c = create_cairo_context()
        c.select_font_face(self.name, cairo.FONT_SLANT_NORMAL)
        c.set_font_size(self.size)
        # add x_bearing to width (maybe use x_advance later)
        # http://cairographics.org/manual/cairo-Scaled-Fonts.html#cairo-text-extents-t
        ext = c.text_extents(text)
        return int(ext[0] + ext[2]) + 1

    def get_font(self, height):
        """
        Get font object with size set to fit the given height.
        """
        size = 1
        last = None
        while True:
            if not self.__height_cache.get((self.name, size)):
                self.get_height(size=size)
            if self.__height_cache.get((self.name, size))[Font.MAX_HEIGHT] > height:
                f = Font(self.name)
                f.size = size - 1
                return f
            last = size
            size += 1

    def get_font_description(self):
        """
        Get the Pango.FontDescription for the font object
        """
        return Pango.FontDescription.from_string("%s %spx" % (self.name, self.size))
