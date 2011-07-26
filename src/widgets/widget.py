__all__ = [ 'Widget' ]

_candy_id = 0
_candy_new = []
_candy_reparent = []

NOT_SET = object()

class BackendCls(object):

    _candy_modified = {}

    def __init__(self):
        self.parent = None

    def prepare(self):
        # kaa mainloop
        pass

    def create(self):
        # clutter thread
        pass

    def reparent(self, parent):
        # clutter thread
        if self.parent:
            self.parent._obj.remove(self._obj)
        self.parent = parent
        if self.parent:
            self.parent._obj.add(self._obj)

    def update(self):
        # clutter thread
        if 'x' in self._candy_modified or 'y' in self._candy_modified:
            self._obj.set_position(self.x, self.y)

class Widget(object):

    BackendCls = BackendCls
    attributes = [ 'x', 'y' ]

    _candy_dirty = True
    _candy_parent_obj = None
    _candy_parent_id = None

    x = 0
    y = 0

    def __init__(self, pos=None, size=None, context=None):
        global _candy_id
        self._candy_id = 0
        if pos is not None:
            self.x, self.y = pos
        _candy_id += 1
        _candy_new.append(self)
        self._candy_cache = {}
        self._candy_id = _candy_id

    def __setattr__(self, attr, value):
        super(Widget, self).__setattr__(attr, value)
        if attr in self.attributes and not self._candy_dirty:
            self._candy_queue_sync()

    def _candy_queue_sync(self):
        """
        Queue sync
        """
        self._candy_dirty = True
        parent = self.parent
        if parent and not parent._candy_dirty:
            parent._candy_queue_sync()

    def _candy_sync(self, tasks):
        if not self._candy_dirty:
            return
        attributes = {}
        for a in self.attributes:
            old_value = self._candy_cache.get(a, NOT_SET)
            new_value = getattr(self, a)
            if old_value != new_value:
                attributes[a] = new_value
                self._candy_cache[a] = new_value
        tasks.append(('modify', self._candy_id, attributes))
        self._candy_dirty = False

    @property
    def parent(self):
        return self._candy_parent_obj

    @parent.setter
    def parent(self, parent):
        if not self in _candy_reparent:
            self._candy_queue_sync()
        self._candy_parent_obj = parent
        if not self in _candy_reparent:
            _candy_reparent.append(self)
            self._candy_queue_sync()
