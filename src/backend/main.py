# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# main - Backend main process
# -----------------------------------------------------------------------------
# $Id: $
#
# -----------------------------------------------------------------------------
# kaa-candy - Third generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer, Jason Tackaberry
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

# python imports
import sys
import os
import time
import threading
import traceback
import imp
import __builtin__
import gobject

# kaa imports
import kaa
import kaa.rpc
import kaa.candy2.core

# cluter wrapper
from wrapper import clutter

class Modules(object):
    """
    Object holding modules imported by the stage
    """
    clutter = clutter
    core = kaa.candy2.core

    def __call__(self, name):
        return getattr(self, name)

# object with all modules imported
candy_module = Modules()

# expose candy_module as some sort of candy import
__builtin__.candy_module = candy_module

class Stage(object):
    """
    Backend stage class
    """
    def __init__(self, name):
        self.ipc = kaa.rpc.Server(name)
        self.ipc.signals['client-connected'].connect(self.ipc_connected)
        self.ipc.register(self)
        self.queue = []
        self.widgets = {}
        self.candy_import('candy', os.path.dirname(__file__) + '/widgets')
        self.sync([])

    def ipc_connected(self, client):
        """
        Callback when the main app connects to the backend
        """
        client.signals['closed'].connect_once(self.ipc_disconnected)

    def ipc_disconnected(self):
        """
        Callback when the main app disconnects from the backend
        """
        sys.exit(0)

    def candy_import(self, name, path):
        """
        Import wrapper inside the backend
        """
        path = os.path.abspath(path)
        basename, dirname = os.path.basename(path), os.path.dirname(path)
        (file, filename, data) = imp.find_module(basename, [ dirname ])
        setattr(candy_module, name, imp.load_module(name, file, filename, data))

    def create(self, size, group):
        """
        Create the clutter stage object
        Executed inside the clutter thread
        """
        self.group = group
        self.obj = clutter.Stage()
        self.obj.set_size(*size)
        self.obj.set_color(clutter.Color(0, 0, 0, 0xff))
        self.obj.add(group.obj)
        self.obj.show()

    def scale(self, factor):
        """
        Scale the stage and the core group object
        Executed inside the clutter thread
        """
        self.group.obj.set_scale(*factor)

    def sync_clutter(self, event):
        """
        Sync the changes with the clutter objects
        Executed inside the clutter thread
        """
        t0 = time.time()
        while self.queue:
            func = self.queue.pop(0)
            try:
                func[0](*func[1:])
            except Exception, e:
                traceback.print_exc()
        print 'sync took %0.4f sec' % (time.time() - t0)
        event.set()
        return False

    @kaa.rpc.expose()
    def sync(self, tasks):
        """
        Sync callback from the candy application
        """
        for cmd, args in tasks:
            print cmd, args
            if cmd == 'stage':
                self.queue.append((self.create, args[0], self.widgets[args[1]]))
            if cmd == 'scale':
                self.queue.append((self.scale, args[0]))
            if cmd == 'add':
                self.widgets[args[1]] = eval('candy_module.' + args[0])()
                self.queue.append((self.widgets[args[1]].create,))
            if cmd == 'reparent':
                if args[1]:
                    self.queue.append((self.widgets[args[0]].reparent, self.widgets[args[1]]))
                else:
                    self.queue.append((self.widgets[args[0]].reparent, None))
            if cmd == 'modify':
                w = self.widgets[args[0]]
                for a, v in args[1].items():
                    setattr(w, a, v)
                try:
                    w.prepare(args[1])
                except Exception, e:
                    traceback.print_exc()
                self.queue.append((w.update, args[1]))
            if cmd == 'delete':
                self.queue.append((self.widgets[args[0]].delete,))
                del self.widgets[args[0]]
        if self.queue:
            # sync with the clutter thread
            event = threading.Event()
            gobject.idle_add(self.sync_clutter, event)
            event.wait()


if __name__ == '__main__':
    # kaa.candy backend process
    clutter.initialize()
    stage = Stage(sys.argv[1])
    kaa.main.run()
