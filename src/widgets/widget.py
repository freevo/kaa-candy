
__all__ = [ 'Widget' ]

import kaa
import kaa.weakref

from .. import candyxml, core

next_candy_id = 1

NOT_SET = object()

class _dict(dict):
    """
    XML parser dict helper class.
    """
    def update(self, **kwargs):
        super(_dict, self).update(**kwargs)
        return self

class BackendWrapper(object):
    def __init__(self, candy_id):
        self.candy_id = candy_id
        self.queue = []
        self.stage = None

    def call(self, cmd, *args):
        if self.stage:
            return self.stage.queue_command(self.candy_id, cmd, args)
        self.queue.append((self.candy_id, cmd, args))
            
    def __getattr__(self, attr):
        return lambda *args: self.call(attr, *args)


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

    # internal object variables
    _candy_dirty = True
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
    # other widgets in a container. Changing a widget from active to
    # passive and the other way around is not allowed once the widget
    # is visible.
    passive = False

    #: set if the object reacts on context
    context_sensitive = False

    # the geometry values depend on some internal calculations.
    # Therefore, they are hidden using properties.
    __x = 0
    __y = 0
    __width = None
    __height = None
    __intrinsic_size = None
    __variable_width = 100
    __variable_height = 100

    __parent = None

    # attributes
    name = None

    xalign = None
    yalign = None

    def __init__(self, pos=None, size=None, context=None):
        global next_candy_id
        self._candy_id = next_candy_id
        next_candy_id += 1
        if pos is not None:
            self.x, self.y = pos
        if size is not None:
            self.width, self.height = size
        Widget._candy_sync_new.append(self)
        self._candy_cache = {}
        self.__context = context or {}
        self.backend = BackendWrapper(self._candy_id)

    def __setattr__(self, attr, value):
        super(Widget, self).__setattr__(attr, value)
        if not self._candy_dirty and (attr in self.attributes or attr in ['xalign', 'yalign']):
            self.queue_rendering()

    def __del__(self):
        if not hasattr(self, '_beacon_id'):
            return
        Widget._candy_sync_delete.append(self._candy_id)
        if self._candy_stage and not self._candy_stage._candy_dirty:
            self._candy_stage.queue_rendering()

    def __sync__(self, tasks):
        if not self._candy_dirty:
            return False
        (x, y), (width, height) = self.intrinsic_geometry
        # check the position and set a new position on the backend if
        # needed. This does not result in a new rendering.
        attributes = {}
        for (attr, value) in [ ('x', x), ('y', y) ]:
            if self._candy_cache.get(attr, NOT_SET) != value:
                attributes[attr] = value
        if attributes:
            self._candy_cache.update(attributes)
            tasks.append(('position', (self._candy_id, x, y)))
        # check all other attributes and this will cause a
        # re-rendering. Even width and height change the widget on the
        # backend.
        attributes = {}
        for attr in self.attributes:
            new_value = getattr(self, attr)
            if self._candy_cache.get(attr, NOT_SET) != new_value:
                attributes[attr] = new_value
        for (attr, value) in [ ('width', width), ('height', height) ]:
            if self._candy_cache.get(attr, NOT_SET) != value:
                attributes[attr] = value
        if attributes:
            self._candy_cache.update(attributes)
            tasks.append(('update', (self._candy_id, attributes)))
        self._candy_dirty = False
        return True

    def prepare_sync(self):
        return self._candy_dirty

    def queue_rendering(self):
        """
        Queue sync
        """
        if self._candy_dirty:
            return True
        self._candy_dirty = True
        self.__intrinsic_size = None
        parent = self.parent
        if parent and not parent._candy_dirty:
            parent.queue_rendering()
        return False

    def calculate_intrinsic_size(self, (width, height)):
        """
        Calculate intrinsic size based on the parent's size
        """
        if self.__variable_width:
            self.__width = int((width * self.__variable_width) / 100)
        if self.__variable_height:
            self.__height = int((height * self.__variable_height) / 100)
        self.__intrinsic_size = self.__width, self.__height
        return self.__intrinsic_size

    def animate(self, ease, secs, *args):
        self.backend.animate(ease, secs, *args)

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x
        if not self._candy_dirty:
            self.queue_rendering()

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y
        if not self._candy_dirty:
            self.queue_rendering()

    @property
    def width(self):
        if self.__width == -1:
            # force calculation
            self.intrinsic_size
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
        if not self._candy_dirty:
            self.queue_rendering()

    @property
    def height(self):
        if self.__height == -1:
            # force calculation
            self.intrinsic_size
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
        if not self._candy_dirty:
            self.queue_rendering()

    @property
    def size(self):
        return self.width, self.height

    @property
    def variable_size(self):
        return self.__variable_width or self.__variable_height

    @property
    def intrinsic_size(self):
        if not self.__intrinsic_size:
            if (self.__variable_width or self.__variable_height) and not self.parent.__intrinsic_size:
                self.parent.intrinsic_size
            else:
                self.calculate_intrinsic_size(self.parent.size)
        return self.__intrinsic_size

    @intrinsic_size.setter
    def intrinsic_size(self, size):
        self.__intrinsic_size = size

    @property
    def intrinsic_geometry(self):
        """
        The actual geometry of the object
        """
        x, y = self.__x, self.__y
        width, height = self.intrinsic_size
        if self.xalign == Widget.ALIGN_CENTER:
            x += int((self.__width - width) / 2)
        if self.xalign == Widget.ALIGN_RIGHT:
            x += int(self.__width - width)
        if self.yalign == Widget.ALIGN_CENTER:
            y += int((self.__height - height) / 2)
        if self.yalign == Widget.ALIGN_BOTTOM:
            y += int(self.__height - height)
        return (x, y), (width, height)

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, parent):
        if not self in Widget._candy_sync_reparent:
            self.queue_rendering()
            if self.__parent:
                self.__parent.children.remove(self)
        self.__parent = kaa.weakref.weakref(parent)
        if not self in Widget._candy_sync_reparent:
            if parent:
                parent.children.append(self)
                parent.queue_rendering()
            Widget._candy_sync_reparent.append(self)
            self.queue_rendering()

    def context_sync(self):
        pass

    @property
    def context(self):
        return self.__context

    @context.setter
    def context(self, context):
        self.__context = context
        self.context_sync()

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
