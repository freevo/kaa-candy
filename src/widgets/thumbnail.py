# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# thumbnail.py - thumbnail widget for kaa.beacon thumbnail objects
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2013 Dirk Meyer
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

__all__ = [ 'Thumbnail' ]

# kaa imports
import kaa.beacon

# kaa.candy imports
from widget import Widget
from image import Image

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
        """
        Set the thumbnail and a default if the thumbnail is invalid
        """
        self.__thumbnail_provided = thumbnail
        self.__default_provided = default
        if isinstance(thumbnail, (str, unicode)):
            # get thumbnail from context
            # FIXME: make this dynamic
            thumbnail = self.context.get(thumbnail)
        item = None
        if isinstance(thumbnail, kaa.beacon.Item):
            item, thumbnail = thumbnail, thumbnail.get('thumbnail')
        self._thumbnail = thumbnail
        if default and not default.startswith('/'):
            default = self.search(default)
        if default:
            self.image = default
        if self._thumbnail is not None:
            # show thumbnail
            self._beacon_thumbnail_ready(force=True)
        elif item is not None and not item.scanned:
            scanning = item.scan()
            if scanning:
                scanning.connect_weak_once(self._beacon_update, item)

    def sync_context(self):
        """
        Adjust to a new context
        """
        self.set_thumbnail(self.__thumbnail_provided, self.__default_provided)

    def _beacon_update(self, changes, item):
        self._thumbnail = item.get('thumbnail')
        if self._thumbnail is not None:
            return self._beacon_thumbnail_ready(force=True)

    def _beacon_thumbnail_ready(self, force=False):
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
                connect_weak_once(self._beacon_thumbnail_ready)

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
          <thumbnail x='10' y='10' width='100' height='100' thumbnail='thumb'/>
        The thumbnail parameter must be a string that will be evaluated based
        on the given context.
        """
        return Widget.candyxml_parse(element).update(
            thumbnail=element.thumbnail, default=element.default)
