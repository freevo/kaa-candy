# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# clone.py - clone widget for another widget
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2013 Dirk Meyer
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

__all__ = [ 'Clone' ]

# python imports
import logging

# kaa imports
import kaa

# kaa.candy imports
from widget import Widget

# get logging object
log = logging.getLogger('kaa.candy')

class Clone(Widget):
    """
    """
    candy_backend = 'candy.Clone'

    def __init__(self, pos=None, master=None):
        super(Clone, self).__init__(pos, None, context={})
        self.master = master
        self.__candy_set_master = True

    def sync_layout(self, size):
        """
        Sync layout is based on the master object
        """
        super(Clone, self).sync_layout(size)
        self.intrinsic_size = self.master.intrinsic_size

    def __sync__(self, tasks):
        """
        Internal function to add the changes to the list of tasks for
        the backend.
        """
        super(Clone, self).__sync__(tasks)
        if self.__candy_set_master:
            self.backend.call('set_master', 'candy:widget:%s' % self.master._candy_id)
            self.__candy_set_master = False
