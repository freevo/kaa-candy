# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# image.py - Imlib2 Widget
# -----------------------------------------------------------------------------
# $Id:$
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

__all__ = [ 'Image' ]

import os
import tempfile

import kaa.imlib2

import widget

class Image(widget.Widget):
    candyxml_name = 'image'
    candy_backend = 'candy.Imlib2Texture'
    attributes = [ 'data', 'modified' ]

    modified = False

    def __init__(self, pos=None, size=None, url=None, context=None):
        """
        Create the Image

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget
        @param url: filename or url of the image. If the image is not found
            config.imagepath will be searched for the image. If the url
            starts with C{$} the url will be searched in the context.
        @param context: the context the widget is created in
        """
        super(Image, self).__init__(pos, size, context)
        self.image = url

    def __sync__(self, tasks):
        if self.modified:
            # The modified flag is set. That also means the widget is
            # already marked dirty. Therefore, it is save to play with
            # self.data and self.modify without triggering the parent
            # again.
            fd, filename = tempfile.mkstemp(prefix='candy', dir='/dev/shm')
            try:
                # write the image data to shm
                os.write(fd, str(self.__imagedata.get_raw_data()))
                self.data = filename, self.__imagedata.size
            finally:
                os.close(fd)
        self.modified = False
        # now we call the super.__sync__ which will reset the dirty
        # flag and sync the data to the backend
        super(Image, self).__sync__(tasks)

    @property
    def image(self):
        return self.__imagedata

    @image.setter
    def image(self, image):
        if isinstance(image, kaa.imlib2.Image):
            self.__imagedata = image
        else:
            self.__imagedata = kaa.imlib2.Image(image)
        self.modified = True

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <image x='10' y='10' width='200' height='100' filename='image.jpg'/>
          <image width='200' height='100' url='http://www.exapmple.com/image.jpg'/>
        """
        return super(Image, cls).candyxml_parse(element).update(
            url=element.url or element.filename)
