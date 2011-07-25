import time
import sys
import subprocess

import kaa
import kaa.rpc
import backend
import threading
import gobject

from widgets import Group
from widgets.widget import _candy_new, _candy_reparent

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
        self._obj = backend.Stage()
        self._obj.set_size(*size)
        self._obj.set_color(backend.Color(0, 0, 0, 0xff))
        self._obj.add(group._obj)
        self._obj.show()

    def _stage_sync(self, event):
        while self._clutter_queue:
            func, args, kwargs = self._clutter_queue.pop(0)
            func(*args, **kwargs)
        event.set()
        return False
        
    @kaa.rpc.expose()
    def sync(self, tasks):
        for t in tasks:
            print t
            if t[0] == 'stage':
                self._clutter_call(self._stage_create, t[1], self._widgets[t[2]])
            if t[0] == 'add':
                self._widgets[t[2]] = t[1]()
            if t[0] == 'reparent':
                widget = self._widgets[t[1]]
                if widget.parent:
                    widget.parent._obj.remove(widget._obj)
                widget.parent = self._widgets[t[2]]
                widget.parent._obj.add(widget._obj)
            if t[0] == 'modify':
                w = self._widgets[t[1]]
                for a, v in t[2].items():
                    setattr(w, a, v)
                w._candy_modified = t[2]
                if w._candy_sync():
                    self._clutter_call(w._clutter_sync)
        event = threading.Event()
        gobject.idle_add(self._stage_sync, event)
        event.wait()


class Stage(object):

    def __init__(self, size, name):
        args = [ 'python', __file__, name ]
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
        self.initialized = False

    def add(self, widget):
        self.group.add(widget)

    def sync(self):
        tasks = []
        while _candy_new:
            widget = _candy_new.pop(0)
            tasks.append(('add', widget.BackendCls, widget._candy_id))
        if not self.initialized:
            self.initialized = True
            tasks.append(('stage', self.size, self.group._candy_id))
        while _candy_reparent:
            widget = _candy_reparent.pop(0)
            tasks.append(('reparent', widget._candy_id, widget.parent._candy_id))
        self.group._backend_sync(tasks)
        self.ipc.rpc('sync', tasks)


if __name__ == '__main__':
    backend.initialize()
    stage = _Stage(sys.argv[1])
    kaa.main.run()
