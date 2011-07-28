
__all__ = [ 'Widget' ]


import candyxml
from core import Modifier

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

class _dict(dict):
    """
    XML parser dict helper class.
    """
    def update(self, **kwargs):
        super(_dict, self).update(**kwargs)
        return self

class Template(object):
    """
    Template to create a widget on demand. All XML parsers will create such an
    object to parse everything at once.
    """

    #: class is a template class
    __is_template__ = True

    def __init__(self, cls, **kwargs):
        """
        Create a template for the given class

        :param cls: widget class
        :param kwargs: keyword arguments for cls.__init__
        """
        self._cls = cls
        self._modifier = kwargs.pop('modifier', [])
        self._kwargs = kwargs
        self._properties = []
        self.userdata = {}

    def set_property(self, key, value):
        """
        Add property to be set after widget creation
        """
        self._properties.append((key, value))

    def __call__(self, context=None, **kwargs):
        """
        Create the widget with the given context and override some
        constructor arguments.

        :param context: context to create the widget in
        :returns: widget object
        """
        if context is not None:
            context = Context(context)
        args = self._kwargs.copy()
        args.update(kwargs)
        if self._cls.context_sensitive:
            args['context'] = context
        widget = self._cls(**args)
        for key, value in self._properties:
            setattr(widget, key, value)
        return widget

    @classmethod
    def candyxml_get_class(cls, element):
        """
        Get the class for the candyxml element. This function may be overwritten
        by inheriting classes and should not be called from outside such a class.
        """
        return candyxml.get_class(element.node, element.style)

    @classmethod
    def candyxml_create(cls, element):
        """
        Parse the candyxml element for parameter and create a Template.
        """
        modifier = []
        for subelement in element.get_children():
            mod = Modifier.candyxml_create(subelement)
            if mod is not None:
                modifier.append(mod)
                element.remove(subelement)
        widget = cls.candyxml_get_class(element)
        if widget is None:
            log.error('undefined widget %s:%s', element.node, element.style)
        kwargs = widget.candyxml_parse(element)
        if modifier:
            kwargs['modifier'] = modifier
        template = cls(widget, **kwargs)
        return template

class Widget(object):

    BackendCls = BackendCls
    attributes = [ 'x', 'y', 'width', 'height' ]

    _candy_dirty = True
    _candy_parent_obj = None
    _candy_parent_id = None

    class __metaclass__(type):
        def __new__(meta, name, bases, attrs):
            cls = type.__new__(meta, name, bases, attrs)
            if 'candyxml_name' in attrs.keys() or 'candyxml_style' in attrs.keys():
                candyxml.register(cls)
            return cls

    #: template for object creation
    __template__ = Template

    #: set if the object reacts on context
    context_sensitive = False

    x = 0
    y = 0
    width = None
    height = None

    def __init__(self, pos=None, size=None, context=None):
        global _candy_id
        self._candy_id = 0
        if pos is not None:
            self.x, self.y = pos
        if size is not None:
            self.width, self.height = size
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
