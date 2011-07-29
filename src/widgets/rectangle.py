__all__ = [ 'Rectangle' ]

import widget
from backend import Rectangle as BackendCls

class Rectangle(widget.Widget):
    candyxml_name = 'rectangle'
    BackendCls = BackendCls
