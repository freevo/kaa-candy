
__all__ = [ 'Widget' ]

import kaa
import kaa.weakref

from kaa.utils import property

from .. import candyxml
from ..core import Modifier

next_candy_id = 1

NOT_SET = object()

class _dict(dict):
    """
    XML parser dict helper class.
    """
    def update(self, **kwargs):
        super(_dict, self).update(**kwargs)
        return self

class Widget(object):

    candy_backend = 'candy.Widget'
    attributes = []

    ALIGN_LEFT = 'left'
    ALIGN_RIGHT = 'right'
    ALIGN_TOP = 'top'
    ALIGN_BOTTOM = 'bottom'
    ALIGN_CENTER = 'center'
    ALIGN_SHRINK = 'shrink'

    # internal class variables
    _candy_sync_new = []
    _candy_sync_delete = []
    _candy_sync_reparent = []

    _candy_dirty = True
    _candy_geometry_dirty = True
    _parent = None
    _candy_parent_id = None
    _candy_stage = None

    class __metaclass__(type):
        def __new__(meta, name, bases, attrs):
            cls = type.__new__(meta, name, bases, attrs)
            if 'candyxml_name' in attrs.keys() or 'candyxml_style' in attrs.keys():
                candyxml.register(cls)
            return cls

    #: template for object creation
    __template__ = candyxml.Template

    # passive widgets with dynamic size depend on the size of the
    # other widgets in a container
    passive = False

    #: set if the object reacts on context
    context_sensitive = False

    # variable size calculation (percent)
    __variable_width = 100
    __variable_height = 100

    # the geometry values depend on some internal calculations.
    # Therefore, they are hidden using properties.
    __x = 0
    __y = 0
    __width = None
    __height = None

    xalign = None
    yalign = None

    def __init__(self, pos=None, size=None, context=None):
        global next_candy_id
        if pos is not None:
            self.x, self.y = pos
        if size is not None:
            self.width, self.height = size
        Widget._candy_sync_new.append(self)
        self._candy_cache = {}
        self._candy_id = next_candy_id
        next_candy_id += 1

    def __setattr__(self, attr, value):
        super(Widget, self).__setattr__(attr, value)
        if not self._candy_dirty and (attr in self.attributes or attr in ['xalign', 'yalign']):
            self.queue_rendering()

    def __del__(self):
        Widget._candy_sync_delete.append(self._candy_id)
        if self._candy_stage and not self._candy_stage._candy_dirty:
            self._candy_stage.queue_rendering()

    def __sync__(self, tasks):
        if not self._candy_dirty:
            return
        attributes = {}
        for a in self.attributes:
            new_value = getattr(self, a)
            if self._candy_cache.get(a, NOT_SET) != new_value:
                attributes[a] = new_value
                self._candy_cache[a] = new_value
        if self._candy_geometry_dirty:
            geometry = self.calculate_clutter_geometry()
            for a in [ 'x', 'y', 'width', 'height' ]:
                if self._candy_cache.get(a, NOT_SET) != geometry[a]:
                    attributes[a] = geometry[a]
                    self._candy_cache[a] = geometry[a]
            self._candy_geometry_dirty = False
        tasks.append(('modify', (self._candy_id, attributes)))
        self._candy_dirty = False

    def queue_rendering(self):
        """
        Queue sync
        """
        self._candy_dirty = True
        parent = self.parent
        if parent and not parent._candy_dirty:
            parent.queue_rendering()

    def queue_layout(self):
        """
        Queue sync for layout changes
        """
        self._candy_dirty = True
        self._candy_geometry_dirty = True
        parent = self.parent
        if parent and not parent._candy_geometry_dirty:
            parent.queue_layout()

    def calculate_variable_geometry(self, (width, height)):
        """
        Calculate variable geometry for given percentage values
        """
        if self.__variable_width:
            self.__width = int((width * self.__variable_width) / 100)
        if self.__variable_height:
            self.__height = int((height * self.__variable_height) / 100)

    def calculate_clutter_geometry(self):
        """
        Calculate the actual geometry of the objects
        """
        geometry = {'x': self.__x, 'y': self.__y}
        width, height = self.intrinsic_size
        if self.xalign == Widget.ALIGN_CENTER:
            geometry['x'] += int((self.__width - width) / 2)
        if self.xalign == Widget.ALIGN_RIGHT:
            geometry['x'] += int(self.__width - width)
        if self.yalign == Widget.ALIGN_CENTER:
            geometry['y'] += int((self.__height - height) / 2)
        if self.yalign == Widget.ALIGN_BOTTOM:
            geometry['y'] += int(self.__height - height)
        geometry['width'] = width
        geometry['height'] = height
        return geometry

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x
        if not self._candy_geometry_dirty:
            self.queue_layout()

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y
        if not self._candy_geometry_dirty:
            self.queue_layout()

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if isinstance(width, (str, unicode)):
            # use percent values provided by the string
            self.__variable_width = int(width[:-1])
            self.__width = -1
        elif width is None:
            self.__variable_width = 100
            self.__width = -1
        else:
            self.__variable_width = None
            self.__width = width
        if not self._candy_geometry_dirty:
            self.queue_layout()

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        if isinstance(height, (str, unicode)):
            # use percent values provided by the string
            self.__variable_height = int(height[:-1])
            self.__height = -1
        elif height is None:
            self.__variable_height = 100
            self.__height = -1
        else:
            self.__variable_height = None
            self.__height = height
        if not self._candy_geometry_dirty:
            self.queue_layout()

    @property
    def intrinsic_size(self):
        return self.__width, self.__height

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if not self in Widget._candy_sync_reparent:
            self.queue_rendering()
            if self._parent:
                self._parent.children.remove(self)
        self._parent = kaa.weakref.weakref(parent)
        if not self in Widget._candy_sync_reparent:
            if parent:
                parent.children.append(self)
            Widget._candy_sync_reparent.append(self)
            self.queue_rendering()

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. This function
        must be overwitten by a subclass for the correct parsing. This class
        only parses pos and size and children with a use-us attribute::
          <widget x='10' y='20' width='100' height='50'>
              <widget x='0' y='0' use-as='content'/>
          </widget>

        This will return a dictionary with pos, size, and content.
        """
        parameter = _dict(pos=element.pos, size=(element.width, element.height))
        for child in element:
            if child.use_as:
                widget = child.xmlcreate()
                if not widget:
                    log.error('unable to parse %s', child.node)
                else:
                    parameter[str(child.use_as)] = widget
                element.remove(child)
        return parameter
