__all__ = [ 'Group' ]

import widget
import backend

class BackendCls(widget.Widget.BackendCls):
    
    def create(self):
        self._obj = backend.Group()
        self._obj.show()
        

class Group(widget.Widget):
    BackendCls = BackendCls

    def __init__(self, pos=None, size=None, context=None):
        super(Group, self).__init__(pos, size, context)
        self.children = []

    def add(self, *widgets):
        """
        Add widgets to the group.
        """
        for widget in widgets:
            # TODO: that should happen in the next line
            self.children.append(widget)
            widget.parent = self

    def _candy_sync(self, tasks):
        super(Group, self)._candy_sync(tasks)
        for child in self.children:
            child._candy_sync(tasks)
        # TODO: check for dirty
