# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# image.py - image widgets
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

__all__ = [ 'CairoTexture', 'Imlib2Texture' ]

import os
import kaa.imlib2

import widget

clutter = candy_module('clutter')

class CairoTexture(widget.Widget):
    """
    Cairo based Texture widget.
    """

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.CairoTexture(self.width, self.height)
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        super(CairoTexture, self).update(modified)
        if ('width' in modified or 'height' in modified) and self.height and self.width:
            self.obj.set_surface_size(self.width, self.height)
        self.obj.clear()


class Imlib2Texture(widget.Widget):
    """
    Imlib2 based Texture widget.
    """

    def prepare(self, modified):
        """
        Prepare rendering
        """
        if 'data' in modified:
            # load the image in the kaa mainloop (it does not have to
            # be this way, we use shared memory; just to use the
            # prepare() function once)
            filename, (width, height) = self.data
            self.imagedata = open(filename).read()
            os.unlink(filename)

    def create(self):
        """
        Create the clutter object
        """
        self.obj = clutter.Texture()
        self.obj.show()

    def update(self, modified):
        """
        Render the widget
        """
        if 'data' in modified:
            filename, (width, height) = self.data
            self.obj.set_from_rgb_data(self.imagedata, True, width, height,
                 width*4, 4, clutter.TEXTURE_RGB_FLAG_BGR)
            del self.imagedata
