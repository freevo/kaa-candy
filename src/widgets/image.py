# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# image.py - image widget based on kaa.imlib2
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

__all__ = [ 'Image', 'resolve_image_url' ]

# python imports
import os
import logging
import hashlib
import tempfile

# kaa imports
import kaa
import kaa.net.url
import kaa.imlib2

# kaa.candy imports
from widget import Widget
from .. import config

# get logging object
log = logging.getLogger('kaa.candy')

def resolve_image_url(name):
    """
    Helper function to get the full path of the image.
    @param name: image filename without path
    """
    for path in config.imagepath:
        filename = os.path.join(path, name)
        if os.path.isfile(filename):
            return filename
    return None

class Image(Widget):
    """
    kaa.imlib2.Imlib2 based image widget
    """
    candyxml_name = 'image'
    candy_backend = 'candy.Imlib2Texture'

    attributes = [ 'data', 'modified', 'keep_aspect' ]

    # image variables
    modified = True
    keep_aspect = False

    # class variable with a dict of images currently loading
    __current_downloads = {}

    __filename = None
    __imagedata = None

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

    def sync_context(self):
        """
        Adjust to a new context
        """
        self.image = self.__image_provided

    def sync_layout(self, size):
        """
        Sync layout changes and calculate intrinsic size based on the
        parent's size.
        """
        if not self.__imagedata:
            self.intrinsic_size = 0, 0
            return 0, 0
        super(Image, self).sync_layout(size)
        width, height = self.size
        if self.keep_aspect:
            aspect = float(self.__imagedata.width) / self.__imagedata.height
            if int(height * aspect) > width:
                height = int(width / aspect)
            else:
                width = int(height * aspect)
            self.intrinsic_size = width, height

    def sync_prepare(self):
        """
        Prepare widget for the next sync with the backend
        """
        if not self.modified:
            return False
        self.data = None, (0, 0)
        if self.__imagedata:
            fd, filename = tempfile.mkstemp(prefix='candy', dir='/dev/shm')
            try:
                # write the image data to shm
                os.write(fd, str(self.__imagedata.get_raw_data()))
                self.data = filename, self.__imagedata.size
            finally:
                self.modified = False
                os.close(fd)
        self.modified = False
        return True

    def on_download_complete(self, status, cachefile):
        """
        Callback for HTTP GET result. The image should be in the
        cachefile.
        """
        if cachefile in self.__current_downloads:
            del self.__current_downloads[cachefile]
        self.image = cachefile

    @property
    def image(self):
        """
        Return the image as kaa.imlib2.Image
        """
        return self.__imagedata

    @image.setter
    def image(self, image):
        """
        Set a new image. Either a kaa.imlib2.Image or based on a
        filename or url.
        """
        self.__image_provided = image
        if image and image.startswith('$'):
            # variable from the context, e.g. $varname
            image = self.context.get(image) or ''
        if isinstance(image, kaa.imlib2.Image):
            self.__imagedata = image
            self.modified = True
            return
        # load image by url/filename
        if image and image.startswith('http://'):
            # remote image, create local cachefile
            # FIXME: how to handle updates on the remote side?
            base = hashlib.md5(image).hexdigest() + os.path.splitext(image)[1]
            cachefile = kaa.tempfile('candy-images/' + base)
            if not os.path.isfile(cachefile):
                # Download the image
                # FIXME: errors will be dropped
                # FIXME: support other remote sources
                # FIXME: use one thread (jobserver) for all downloads
                #  or at least a max number of threads to make the individual
                #  image loading faster
                if not cachefile in self.__current_downloads:
                    tmpfile = kaa.tempfile('candy-images/.' + base)
                    c = kaa.net.url.fetch(image, cachefile, tmpfile)
                    self.__current_downloads[cachefile] = c
                self.__current_downloads[cachefile].connect_weak_once(self.on_download_complete, cachefile)
                image = None
            else:
                image = cachefile
        if image and not image.startswith('/'):
            image = resolve_image_url(image)
        if self.__filename == image:
            return
        self.__filename = image
        try:
            if image:
                self.__imagedata = kaa.imlib2.Image(image)
            else:
                self.__imagedata = None
        except Exception, e:
            log.error('unable to load %s', image)
            self.__imagedata = None
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
