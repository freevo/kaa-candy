# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# main - Backend main process
# -----------------------------------------------------------------------------
# The candy server will run an RPC server in the kaa mainloop and will
# execute commands. A widget is created and prepared in the kaa main
# loop; everything else, including imports is done in the clutter
# thread.
#
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011-2012 Dirk Meyer
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

# python imports
import sys
import os
import time
import threading
import imp
import logging
import logging.config
import logging.handlers

# get logging object
log = logging.getLogger('candy')

# import GObject from gi.repository before jumping into kaa to force
# kaa.gobject to use the gi repository
from gi.repository import GObject as gobject

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
            from gi.repository import Clutter as clutter
            clutter.threads_init()
            clutter.init([])
            clutter.main()
        except Exception, e:
            log.exception('unable to import clutter')
            return

    def quit(self):
        # Import clutter only in the gobject thread
        from gi.repository import Clutter as clutter
        clutter.main_quit()

    def imp(self, name, path, server):
        """
        Import inside the clutter thread
        """
        path = os.path.abspath(path)
        basename, dirname = os.path.basename(path), os.path.dirname(path)
        (file, filename, data) = imp.find_module(basename, [ dirname ])
        # hack to provide the module to other modules for import
        sys.modules[name] = imp.load_module(name, file, filename, data)
        globals()[name] = sys.modules[name]
        if hasattr(sys.modules[name], 'init'):
            sys.modules[name].init(server)

    def sync(self, queue, event):
        """
        Sync the changes with the clutter objects
        Executed inside the clutter thread
        """
        t0 = time.time()
        freeze = False
        while queue:
            func, args = queue.pop(0)
            if func == 'freeze':
                # Freeze the scene. From now on it is not allowed to
                # go back to the clutter main loop to keep animations
                # alive or the user will see a half-finished scene.
                freeze = True
                continue
            try:
                func(*args)
            except Exception, e:
                log.exception('sync error: %s%s', func, args)
            if not freeze and queue:
                sync_time = time.time() - t0
                if sync_time > 0.01:
                    # We should use the logging module somehow and get the
                    # logging info to the main process. Only print out the
                    # sync time if we cannot make 100fps.
                    log.warning('sync took %0.4f sec' % sync_time)
                    # For further debug to detect what function /
                    # widget is slow taht it took way too long:
                    # print 'last call', func, args
                if sync_time > 0.001:
                    # Not finished yet, but the scene is not frozen
                    # and we can go back to the clutter main loop to
                    # keep animations alive.
                    return True
        sync_time = time.time() - t0
        if sync_time > 0.01:
            # We should use the logging module somehow and get the
            # logging info to the main process. Only print out the
            # sync time if we cannot make 100fps.
            log.warning('kaa.candy warning: sync took %0.4f sec' % sync_time)
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
        self.initialized = False

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
        log.info('client disconnected, shutdown candy subprocess')
        sys.exit(0)

    @kaa.threaded(kaa.MAINTHREAD)
    def send_event(self, event, *args):
        self.ipc.rpc('event_%s' % event.replace('-', '_'), *args)

    @kaa.rpc.expose()
    def sync(self, tasks):
        """
        Sync callback from the candy application
        """
        if not self.initialized:
            self.initialized = True
            self.sync([
                    ('import', ('candy', os.path.dirname(__file__) + '/widgets')),
                    ('import', ('player', os.path.dirname(__file__) + '/player')),
                    ('import', ('stage', os.path.dirname(__file__) + '/stage')),
            ])
        queue = []
        for cmd, args in tasks:
            if cmd == 'freeze':
                # freeze meta-command after that the sync function in
                # the clutter thread is not allowed to go back to its
                # main loop to keep animations alive.
                queue.append(('freeze', None))
                continue
            func = getattr(self, 'cmd_' + cmd, None)
            if func:
                try:
                    delayed = func(*args)
                    if delayed:
                        queue.append(delayed)
                except Exception, e:
                    log.exception('sync error: %s%s', func, args)
            else:
                log.error('unsupported command: %s', cmd)
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
        return mainloop.imp, (name, path, self)

    def cmd_add(self, cls, wid):
        """
        command for sync: add a new widget based on cls with the given wid
        """
        self.widgets[wid] = eval(cls)()
        self.widgets[wid].server = self
        self.widgets[wid].wid = wid
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

    def cmd_reparent(self, child, parent, pos):
        """
        command for sync: reparent the child
        """
        if parent:
            return self.widgets[child].reparent, (self.widgets[parent], self.widgets.get(pos))
        return self.widgets[child].reparent, (None, None)

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

#
# Set up logging module
#
logger = logging.getLogger()

# remove handler, we want to set the look and avoid duplicate handlers
for l in logger.handlers[:]:
    logger.removeHandler(l)

# set stdout logging
formatter = logging.Formatter('%(levelname)s candy:%(module)s(%(lineno)s): %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

if sys.argv[2]:
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)6s] %(filename)s %(lineno)s: %(message)s')
    handler = logging.handlers.RotatingFileHandler(sys.argv[2], maxBytes=1000000, backupCount=2)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# set log level
logger.setLevel(logging.INFO)

kaa.main.init('generic')
kaa.gobject_set_threaded(mainloop)
Server(sys.argv[1])
kaa.main.run()
