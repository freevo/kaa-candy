# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# thumbnail.py - kaa.beacon.Thumbnail Widget
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

__all__ = [ 'Thumbnail' ]

import os
import hashlib
import tempfile

import kaa
import kaa.net.url
import kaa.imlib2

import widget
from image import Image, resolve_image_url

class Thumbnail(Image):
    """
    Widget showing a kaa.beacon.Thumbnail
    """
    candyxml_name = 'thumbnail'
    keep_aspect = True

    def __init__(self, pos, size, thumbnail=None, default=None, context=None):
        """
        Create the Thumbnail widget

        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget
        @param thumbnail: kaa.beacon.Thumbnail object or a string which points
            to the Thumbnail object in the context.
        @param context: the context the widget is created in
        """
        super(Thumbnail, self).__init__(pos, size, context=context)
        self.set_thumbnail(thumbnail, default)

    def set_thumbnail(self, thumbnail, default=None):
        if isinstance(thumbnail, (str, unicode)):
            # get thumbnail from context
            # FIXME: make this dynamic
            thumbnail = self.context.get(thumbnail)
        item = None
        if hasattr(thumbnail, 'scan'):
            # FIXME: bad detection
            # thumbnail is a kaa.beacon.Item
            item, thumbnail = thumbnail, thumbnail.get('thumbnail')
        self._thumbnail = thumbnail
        if self._thumbnail is not None:
            # show thumbnail
            self.show_thumbnail(force=True)
            return
        if default and not default.startswith('/'):
            default = resolve_image_url(default)
        if default:
            self.image = default
        if item is not None and not item.scanned:
            scanning = item.scan()
            if scanning:
                scanning.connect_weak_once(self.beacon_update, item)

    def beacon_update(self, changes, item):
        self._thumbnail = item.get('thumbnail')
        if self._thumbnail is not None:
            return self.show_thumbnail(force=True)

    def show_thumbnail(self, force=False):
        """
        Callback to render the thumbnail to the texture.
        @todo: add thumbnail update based on beacon mtime
        @todo: try to force large thumbnails
        """
        image = self._thumbnail.image
        if image:
            self.image = image
        elif self._thumbnail.failed:
            return False
        if force and self._thumbnail.needs_update:
            # Create thumbnail; This object will hold a reference to the
            # beacon.Thumbnail object and uses high priority. Since we
            # only connect weak to the result we loose the thumbnail object
            # when this widget is removed which will reduce the priority
            # to low. This is exactly what we want. The create will be
            # scheduled in the mainloop but since we do not wait it is ok.
            self._thumbnail.create(self._thumbnail.PRIORITY_HIGH).\
                connect_weak_once(self.show_thumbnail)

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <thumbnail x='10' y='10' width='100' height='100' thumbnail='thumb'/>
        The thumbnail parameter must be a string that will be evaluated based
        on the given context.
        """
        return widget.Widget.candyxml_parse(element).update(
            thumbnail=element.thumbnail, default=element.default)
