class Widget(object):

    _candy_modified = {}

    obj = None

    def __init__(self):
        self.parent = None

    def prepare(self):
        # kaa mainloop
        pass

    def create(self):
        # clutter thread
        pass

    def delete(self):
        # clutter thread
        if not self.obj:
            return
        if self.parent and self.parent.obj:
            self.parent.obj.remove(self.obj)
        self.obj = None

    def reparent(self, parent):
        # clutter thread
        if self.parent:
            self.parent.obj.remove(self.obj)
        self.parent = parent
        if self.parent:
            self.parent.obj.add(self.obj)

    def update(self):
        # clutter thread
        if 'x' in self._candy_modified or 'y' in self._candy_modified:
            self.obj.set_position(self.x, self.y)

