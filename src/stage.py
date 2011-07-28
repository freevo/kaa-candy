import os
import time
import sys
import fcntl
import subprocess

import kaa
import kaa.rpc
import backend
import threading
import gobject

from widgets import Group
from widgets.widget import _candy_new, _candy_reparent
import candyxml

class _Stage(object):

    def __init__(self, name):
        self.ipc = kaa.rpc.Server(name)
        self.ipc.signals['client-connected'].connect(self._ipc_connected)
        self.ipc.register(self)
        self._clutter_queue = []
        self._widgets = {}
        self.sync([])

    def _ipc_connected(self, client):
        client.signals['closed'].connect_once(self._ipc_disconnected)

    def _ipc_disconnected(self):
        sys.exit(0)

    def _clutter_call(self, func, *args, **kwargs):
        self._clutter_queue.append((func, args, kwargs))

    def _stage_create(self, size, group):
        self.group = group
        self._obj = backend.Stage()
        self._obj.set_size(*size)
        self._obj.set_color(backend.Color(0, 0, 0, 0xff))
        self._obj.add(group._obj)
        self._obj.show()

    def _stage_scale(self, factor):
        self.group._obj.set_scale(*factor)

    def _stage_sync(self, event):
        while self._clutter_queue:
            func, args, kwargs = self._clutter_queue.pop(0)
            try:
                func(*args, **kwargs)
            except Exception, e:
                print e
        event.set()
        return False

    @kaa.rpc.expose()
    def sync(self, tasks):
        for t in tasks:
            print t
            if t[0] == 'stage':
                self._clutter_call(self._stage_create, t[1], self._widgets[t[2]])
            if t[0] == 'scale':
                self._clutter_call(self._stage_scale, t[1])
            if t[0] == 'add':
                self._widgets[t[2]] = t[1]()
                self._clutter_call(self._widgets[t[2]].create)
            if t[0] == 'reparent':
                self._clutter_call(self._widgets[t[1]].reparent, self._widgets[t[2]])
            if t[0] == 'modify':
                w = self._widgets[t[1]]
                for a, v in t[2].items():
                    setattr(w, a, v)
                w._candy_modified = t[2]
                try:
                    w.prepare()
                except Exception, e:
                    print e
                self._clutter_call(w.update)
        event = threading.Event()
        gobject.idle_add(self._stage_sync, event)
        event.wait()


class Stage(object):

    def __init__(self, size, name):
        args = [ 'python', __file__, name ]
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
        self.group = Group()
        self.group._candy_parent_obj = self
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

    def _candy_queue_sync(self):
        """
        Queue sync
        """
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
        while _candy_new:
            widget = _candy_new.pop(0)
            tasks.append(('add', widget.BackendCls, widget._candy_id))
        if not self.initialized:
            self.initialized = True
            tasks.append(('stage', self.size, self.group._candy_id))
        if self.scale:
            tasks.append(('scale', self.scale))
            self.scale = None
        while _candy_reparent:
            widget = _candy_reparent.pop(0)
            tasks.append(('reparent', widget._candy_id, widget.parent._candy_id))
        self.group._candy_sync(tasks)
        if tasks:
            self.ipc.rpc('sync', tasks)

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


if __name__ == '__main__':
    backend.initialize()
    stage = _Stage(sys.argv[1])
    kaa.main.run()
