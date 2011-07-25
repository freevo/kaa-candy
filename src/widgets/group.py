__all__ = [ 'Group' ]

import widget
import backend

class BackendCls(widget.Widget.BackendCls):
    
    def __init__(self):
        super(BackendCls, self).__init__()
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

    def _backend_sync(self, tasks):
        super(Group, self)._backend_sync(tasks)
        for child in self.children:
            child._backend_sync(tasks)
        # TODO: check for dirty
