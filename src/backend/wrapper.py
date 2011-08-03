# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# wrapper - Clutter handling and wrapper
# -----------------------------------------------------------------------------
# $Id: $
#
# Access clutter functions and objects
#
# The clutter modules must be imported and used by the gobject mainloop. This
# modules wraps access to all functions, modules and other extensions of clutter
# into a single module. In the clutter mainloop you can clutter by replacing
# clutter with backend.
#
# Special clases inheriting from clutter classes will also be defined in this
# module and imported into the backend namespace when the gobject mainloop starts.
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

__all__ = [ 'clutter' ]

# python imports
import logging
import kaa

# get logging object
log = logging.getLogger('candy')

class Wrapper(object):
    """
    Clutter wrapper class
    """

    class Mainloop(object):
        """
        Clutter mainloop.
        """

        def run(self):
            # Import clutter only in the gobject thread
            # This function will be the running mainloop
            try:
                import clutter as backend
            except Exception, e:
                log.exception('unable to import clutter')
                return
            for key in dir(backend):
                if key[0].isalpha():
                    setattr(clutter, key, getattr(backend, key))
            clutter.threads_init()
            clutter.init()
            # now add some C stuff we have in kaa.candy
            import libcandy
            for key in dir(libcandy):
                if not key.startswith('_'):
                    setattr(clutter, key, getattr(libcandy, key))
            clutter.main()

        def quit(self):
            # Import clutter only in the gobject thread
            import clutter as backend
            clutter.main_quit()

    def initialize(self):
        """
        Set generic mainloop and start the clutter thread
        """
        kaa.main.init('generic')
        kaa.gobject_set_threaded(self.Mainloop())

# global clutter object
clutter = Wrapper()
