# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# main - Backend main process
# -----------------------------------------------------------------------------
# $Id: $
#
# The candy server will run an RPC server in the kaa mainloop and will
# execute commands. A widget is created and prepared in the kaa main
# loop; everything else, including imports is done in the clutter
# thread.
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

# python imports
import sys
import os
import time
import threading
import traceback
import imp
import gobject

# kaa imports
import kaa
import kaa.rpc

# hack to provide the kaa.candy core to the widgets
import kaa.candy.core
sys.modules['core'] = kaa.candy.core

class Mainloop(object):
    """
    Clutter mainloop.
    """

    def run(self):
        # Import clutter only in the gobject thread
        # This function will be the running mainloop
        try:
            import clutter
            clutter.threads_init()
            clutter.init()
            clutter.main()
        except Exception, e:
            log.exception('unable to import clutter')
            return

    def quit(self):
        # Import clutter only in the gobject thread
        import clutter
        clutter.main_quit()

    def imp(self, name, path):
        """
        Import inside the clutter thread
        """
        path = os.path.abspath(path)
        basename, dirname = os.path.basename(path), os.path.dirname(path)
        (file, filename, data) = imp.find_module(basename, [ dirname ])
        # hack to provide the module to other modules for import
        sys.modules[name] = imp.load_module(name, file, filename, data)
        globals()[name] = sys.modules[name]

    def sync(self, queue, event):
        """
        Sync the changes with the clutter objects
        Executed inside the clutter thread
        """
        t0 = time.time()
        while queue:
            func, args = queue.pop(0)
            try:
                func(*args)
            except Exception, e:
                traceback.print_exc()
        sync_time = time.time() - t0
        if sync_time > 0.01:
            # only print out the sync time if we cannot make
            # 100fps. Below is always high enough
            print 'sync took %0.4f sec' % sync_time
        event.set()
        return False

# global mainloop object
mainloop = Mainloop()

class Server(object):
    """
    Backend server class
    """
    def __init__(self, name):
        self.ipc = kaa.rpc.Server(name)
        self.ipc.signals['client-connected'].connect(self.ipc_connected)
        self.ipc.register(self)
        self.widgets = {}
        self.sync([
                ('import', ('candy', os.path.dirname(__file__) + '/widgets')),
                ('import', ('stage', os.path.dirname(__file__) + '/stage'))
        ])

    def ipc_connected(self, client):
        """
        Callback when the main app connects to the backend
        """
        client.signals['closed'].connect_once(self.ipc_disconnected)
        self.ipc = client

    def ipc_disconnected(self):
        """
        Callback when the main app disconnects from the backend
        """
        sys.exit(0)

    @kaa.threaded(kaa.MAINTHREAD)
    def send_event(self, event, *args):
        self.ipc.rpc('event_%s' % event.replace('-', '_'), *args)

    @kaa.rpc.expose()
    def sync(self, tasks):
        """
        Sync callback from the candy application
        """
        queue = []
        for cmd, args in tasks:
            func = getattr(self, 'cmd_' + cmd, None)
            if func:
                try:
                    delayed = func(*args)
                    if delayed:
                        queue.append(delayed)
                except Exception, e:
                    traceback.print_exc()
            else:
                print 'unsupported command: %s' % cmd
        if queue:
            # sync with the clutter thread
            event = threading.Event()
            # FIXME: idle_add does not work when animations are
            # running. It seems to be that clutter uses as much CPU
            # time as possible, nothing is idle.
            gobject.timeout_add(0, mainloop.sync, queue, event)
            event.wait()

    def cmd_import(self, name, path):
        """
        command for sync: import the module with path as name
        """
        return mainloop.imp, (name, path)

    def cmd_add(self, cls, wid):
        """
        command for sync: add a new widget based on cls with the given wid
        """
        self.widgets[wid] = eval(cls)()
        self.widgets[wid].server = self
        return self.widgets[wid].create, ()

    def cmd_call(self, wid, cmd, args):
        """
        command for sync: call the command with args on the given widget
        """
        args = list(args)
        for pos, value in enumerate(args):
            if isinstance(value, (str, unicode)) and value.startswith('candy:widget'):
                args[pos] = self.widgets[int(value[13:])]
        return getattr(self.widgets[wid], cmd), args

    def cmd_reparent(self, child, parent):
        """
        command for sync: reparent the child
        """
        if parent:
            return self.widgets[child].reparent, (self.widgets[parent],)
        return self.widgets[child].reparent, (None,)

    def cmd_position(self, wid, x, y):
        """
        command for sync: set a new position
        """
        w = self.widgets[wid]
        w.x = x
        w.y = y
        return w.set_position, ()

    def cmd_update(self, wid, modified):
        """
        command for sync: update the given widget
        """
        w = self.widgets[wid]
        for a, v in modified.items():
            setattr(w, a, v)
        w.prepare(modified)
        return w.update, (modified,)

    def cmd_delete(self, wid):
        """
        command for sync: delete the given widget
        """
        return self.widgets.pop(wid).delete, ()


kaa.main.init('generic')
kaa.gobject_set_threaded(mainloop)
Server(sys.argv[1])
kaa.main.run()
