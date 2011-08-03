__all__ = [ 'Rectangle' ]

import widget
from ..core import Color

class Rectangle(widget.Widget):
    candyxml_name = 'rectangle'
    candy_backend = 'candy.Rectangle'
    attributes = widget.Widget.attributes + [ 'color' ]

    def __init__(self, pos=None, size=None, color=Color(0,0,0), context=None):
        super(Rectangle, self).__init__(pos, size, context)
        self.color = color

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
            <rectangle x='0' y='0' width='100' height='100' color='0xff0000'/>
        """
        return super(Rectangle, cls).candyxml_parse(element).update(
            color=element.color)
