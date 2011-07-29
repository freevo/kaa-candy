import sys
import os
import threading
import traceback
import gobject

import kaa
import kaa.rpc

from wrapper import clutter

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
        self.obj = clutter.Stage()
        self.obj.set_size(*size)
        self.obj.set_color(clutter.Color(0, 0, 0, 0xff))
        self.obj.add(group.obj)
        self.obj.show()

    def _stage_scale(self, factor):
        self.group.obj.set_scale(*factor)

    def _stage_sync(self, event):
        while self._clutter_queue:
            func, args, kwargs = self._clutter_queue.pop(0)
            try:
                func(*args, **kwargs)
            except Exception, e:
                traceback.print_exc()
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
                self._widgets[t[2]] = t[1](clutter)
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


if __name__ == '__main__':
    clutter.initialize()
    stage = _Stage(sys.argv[1])
    kaa.main.run()
