# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# progressbar.py - progressbar widget
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

__all__ = [ 'Progressbar' ]

# kaa imports
from kaa.utils import property

# kaa.candy imports
from .. import is_template
from rectangle import Rectangle
from group import AbstractGroup
from widget import Widget

class Progressbar(AbstractGroup):
    """
    Widget showing a progressbar. Only the bar is drawn, the border has
    to be created ouside this widget.
    """
    candyxml_name = 'progressbar'

    __max = 0
    __progress = 0

    def __init__(self, pos=None, size=None, progress=None, context=None):
        super(Progressbar, self).__init__(pos, size, context)
        if is_template(progress):
            progress = progress()
        if progress is None:
            # we have no progress bar, use a simple rectangle with its
            # default values. In most cases this is wrong
            progress = Rectangle()
        self.__bar = progress
        self.__bar.x = 0
        self.__bar.y = 0
        self.add(self.__bar)

    @property
    def max(self):
        return self.__max

    @max.setter
    def max(self, value):
        self.__max = value

    @property
    def progress(self):
        return self.__progress

    @progress.setter
    def progress(self, value):
        """
        Set a new progress and redraw the widget.
        """
        self.__progress = value
        self.queue_rendering()

    def inc(self):
        """
        Increase progress by one
        """
        self.__progress += 1
        self.queue_rendering()

    def sync_layout(self, size):
        """
        Sync layout changes and calculate intrinsic size based on the
        parent's size.
        """
        Widget.sync_layout(self, size)
        pos = float(self.__progress) / max(self.__max, self.__progress, 0.1)
        self.__bar.width = int(max(pos * self.width, 1))

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the XML element for parameter to create the widget.
        """
        return super(Progressbar, cls).candyxml_parse(element).update(
            progress=element[0].xmlcreate())
