class Widget(object):

    # clutter object
    obj = None
    # candy parent object
    parent = None

    def prepare(self, modified):
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

    def update(self, modified):
        # clutter thread
        if 'x' in modified or 'y' in modified:
            self.obj.set_position(self.x, self.y)
