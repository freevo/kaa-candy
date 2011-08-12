import os
import time
import sys
import fcntl
import subprocess

import kaa
import kaa.rpc
import threading

from widgets import Group, Widget
import candyxml

class StageGroup(Group):
    def __init__(self, stage, size):
        super(StageGroup, self).__init__(size=size)
        self.stage = stage

    @property
    def parent(self):
        return self.stage

class Stage(object):

    def __init__(self, size, name):
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
        self.size = size
        # create the base widget
        self.group = StageGroup(self, size=size)
        # We need the render pipe, the 'step' signal is not enough. It
        # is not triggered between timer and select and a change done
        # in a timer may get lost.
        self._render_pipe = os.pipe()
        fcntl.fcntl(self._render_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self._render_pipe[1], fcntl.F_SETFL, os.O_NONBLOCK)
        kaa.IOMonitor(self.sync).register(self._render_pipe[0])
        os.write(self._render_pipe[1], '1')
        self.initialized = False
        self.scale = None

    def add(self, widget):
        self.group.add(widget)

    def queue_rendering(self):
        """
        Queue sync
        """
        if not self._candy_dirty:
            self._candy_dirty = True
            os.write(self._render_pipe[1], '1')

    def sync(self):
        # read the socket to handle the sync
        try:
            os.read(self._render_pipe[0], 1)
        except OSError:
            pass
        self._candy_dirty = False
        tasks = []
        while Widget._candy_sync_new:
            widget = Widget._candy_sync_new.pop(0)
            widget._candy_stage = self
            tasks.append(('add', (widget.candy_backend, widget._candy_id)))
        if not self.initialized:
            self.initialized = True
            tasks.append(('stage', (self.size, self.group._candy_id)))
        if self.scale:
            tasks.append(('scale', (self.scale,)))
            self.scale = None
        while Widget._candy_sync_reparent:
            widget = Widget._candy_sync_reparent.pop(0)
            if widget.parent:
                tasks.append(('reparent', (widget._candy_id, widget.parent._candy_id)))
            else:
                tasks.append(('reparent', (widget._candy_id, None)))
        self.group.__sync__(tasks)
        while Widget._candy_sync_delete:
            tasks.append(('delete', (Widget._candy_sync_delete.pop(0),)))
        if tasks:
            for t in tasks:
                print '', t
            self.ipc.rpc('sync', tasks)
        print 'sync'

    def set_content_geometry(self, size):
        if isinstance(size, (str, unicode)):
            size = int(size.split('x')[0]), int(size.split('x')[1])
        self._candy_dirty = True
        self.scale = (float(self.size[0]) / size[0], float(self.size[1]) / size[1])

    def candyxml(self, data):
        """
        Load a candyxml file based on the given screen resolution.

        @param data: filename of the XML file to parse or XML data
        @returns: root element attributes and dict of parsed elements
        """
        return candyxml.parse(data, self.size)
