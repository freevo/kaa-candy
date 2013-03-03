# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# image.py - image widgets
# -----------------------------------------------------------------------------
# This file is imported by the backend process in the clutter
# mainloop. Importing and using clutter is thread-safe.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2012 Dirk Meyer
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

__all__ = [ 'CairoTexture', 'ImageTexture' ]

import os

import cairo
from gi.repository import Clutter as clutter

import widget

class CairoTexture(widget.Widget):
    """
    Cairo based Texture widget.
    """

    width = height = 0

    def create(self):
        """
        Create the clutter object
        """
        if not self.width or not self.height:
            self.width = self.height = 1
        self.obj = clutter.CairoTexture(
            width=self.width, height=self.height,
            surface_width=self.width, surface_height=self.height,
            auto_resize=True)
        self.obj.connect_after('draw', self.draw)
        self.obj.show()

    def draw(self, texture, cr):
        cr.set_operator (cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return True

    def update(self, modified):
        """
        Render the widget
        """
        super(CairoTexture, self).update(modified)
        if ('width' in modified or 'height' in modified) and self.height and self.width:
            self.obj.set_surface_size(self.width, self.height)
        for attribute in 'opacity', 'scale_x', 'scale_y', 'anchor_point':
            if attribute in modified:
                modified.pop(attribute)
        if modified:
            self.obj.invalidate()

class ImageTexture(widget.Widget):
    """
    Image widget.
    """

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.Texture.new()
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        super(ImageTexture, self).update(modified)
        if 'sync_data' in modified and self.sync_data:
            filename, delete = self.sync_data
            # TODO: the prepare function should always load the cogl
            # texture in the main thread to avoid blocking the clutter
            # thread. Loading the image here using kaa.imlib2 and
            # putting the raw data on the texture is actually slower
            # sometimes.
            if self.load_async:
                self.obj.set_load_async(True)
            self.obj.set_from_file(filename)
            if delete:
                os.unlink(filename)
