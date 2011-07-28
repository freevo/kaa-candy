__all__ = [ 'Rectangle' ]

import widget
import backend

class BackendCls(widget.Widget.BackendCls):

    def create(self):
        self._obj = backend.Rectangle()
        self._obj.set_color(backend.Color(60, 60, 0, 0xff))
        self._obj.set_size(self.width, self.height)
        self._obj.show()

class Rectangle(widget.Widget):
    candyxml_name = 'rectangle'
    BackendCls = BackendCls
