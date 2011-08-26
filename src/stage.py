# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# stage.py - Stage class as base for all widgets
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

# python imports
import os
import time
import sys
import fcntl
import subprocess
import threading

# kaa imports
import kaa
import kaa.rpc

# kaa.candy imports
from widgets import Group, Widget
import candyxml

# turn on internal debug
DEBUG = False

class StageGroup(Group):
    """
    Group on the stage as parent for widgets added to the stage.
    """
    def __init__(self, stage, size):
        super(StageGroup, self).__init__(size=size)
        self.stage = stage

    @property
    def parent(self):
        return self.stage

class Stage(object):
    """
    The stage class is the visible window

    @ivar signals: kaa.Signal dictionary for the object
      - key-press: sends a key pressed in the window. The signal is emited in
           the kaa mainloop.
    """
    def __init__(self, size, name):
        self.signals = kaa.Signals('key-press')
        # spawn the backend process
        name = 'candy-backend-%s' % name
        args = [ 'python', os.path.dirname(__file__) + '/backend/main.py', name ]
        self._candy_dirty = True
        self.server = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
        retry = 50
        while True:
            try:
                self.ipc = kaa.rpc.connect(name)
                kaa.inprogress(self.ipc).wait()
                break
            except Exception, e:
                retry -= 1
                if retry == 0:
                    raise e
                time.sleep(0.1)
        self.ipc.register(self)
        self.size = size
        # create the base widget
        self.group = StageGroup(self, size=size)
        # We need the render pipe, the 'step' signal is not enough. It
        # is not triggered between timer and select and a change done
        # in a timer may get lost.
        self._render_pipe = os.pipe()
        fcntl.fcntl(self._render_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self._render_pipe[1], fcntl.F_SETFL, os.O_NONBLOCK)
        kaa.IOMonitor(self.__sync).register(self._render_pipe[0])
        os.write(self._render_pipe[1], '1')
        self.initialized = False
        self.scale = None
        self.commands = []

    def add(self, *widgets):
        """
        Add the given widgets to the stage
        """
        self.group.add(*widgets)

    def remove(self, *widgets):
        """
        Remove the given widgets from the stage
        """
        self.group.remove(*widgets)

    def queue_rendering(self):
        """
        Queue sync for rendering
        """
        if not self._candy_dirty:
            self._candy_dirty = True
            os.write(self._render_pipe[1], '1')

    def queue_command(self, candy_id, cmd, args):
        """
        Queue sync for a command
        """
        self.commands.append((candy_id, cmd, args))
        if not self._candy_dirty:
            self._candy_dirty = True
            os.write(self._render_pipe[1], '1')

    def __sync(self):
        """
        Sync callback when something changed
        """
        # read the socket to handle the sync
        try:
            os.read(self._render_pipe[0], 1)
        except OSError:
            pass
        self._candy_dirty = False
        tasks = []
        # prepare all widgets for the sync
        self.group.sync_prepare()
        # create new widgets
        while Widget._candy_sync_new:
            widget = Widget._candy_sync_new.pop(0)
            widget._candy_stage = self
            widget.backend.stage = self
            while widget.backend.queue:
                self.commands.append(widget.backend.queue.pop(0))
            tasks.append(('add', (widget.candy_backend, widget._candy_id)))
        # create stage object if needed
        if not self.initialized:
            self.initialized = True
            tasks.append(('add', ('stage.Stage', -1)))
            tasks.append(('call', (-1, 'init', (self.size, 'candy:widget/%s' % self.group._candy_id))))
        # scale stage object if needed
        if self.scale:
            tasks.append(('call', (-1, 'scale', (self.scale,))))
            self.scale = None
        # change parents for the widgets
        while Widget._candy_sync_reparent:
            widget = Widget._candy_sync_reparent.pop(0)
            if widget.parent:
                tasks.append(('reparent', (widget._candy_id, widget.parent._candy_id)))
            else:
                tasks.append(('reparent', (widget._candy_id, None)))
        # sync all children
        self.group.__sync__(tasks)
        # add commands for the widgets
        while self.commands:
            tasks.append(('call', self.commands.pop(0)))
        while Widget._candy_sync_delete:
            tasks.append(('delete', (Widget._candy_sync_delete.pop(0),)))
        # now send everything to the backend
        if tasks:
            if DEBUG:
                print 'sync'
                for t in tasks:
                    print '', t
                print
            self.ipc.rpc('sync', tasks)

    def set_content_geometry(self, size):
        """
        Set the geometry. This will scale the group in the stage
        """
        if isinstance(size, (str, unicode)):
            size = int(size.split('x')[0]), int(size.split('x')[1])
        self._candy_dirty = True
        self.scale = (float(self.size[0]) / size[0], float(self.size[1]) / size[1])

    @kaa.rpc.expose()
    def event_key_press(self, key):
        """
        Callback from the backend n key press
        """
        self.signals['key-press'].emit(key)

    def candyxml(self, data):
        """
        Load a candyxml file based on the given screen resolution.

        @param data: filename of the XML file to parse or XML data
        @returns: root element attributes and dict of parsed elements
        """
        return candyxml.parse(data, self.size)
