
__all__ = [ 'Widget' ]

import kaa
import kaa.weakref

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
    attributes = [ 'x', 'y', 'width', 'height' ]

    # internal class variables
    _candy_sync_new = []
    _candy_sync_delete = []
    _candy_sync_reparent = []

    _candy_dirty = True
    _candy_parent_obj = None
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

    #: set if the object reacts on context
    context_sensitive = False

    x = 0
    y = 0
    width = None
    height = None

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
        if attr in self.attributes and not self._candy_dirty:
            self._candy_queue_sync()

    def __del__(self):
        Widget._candy_sync_delete.append(self._candy_id)
        if self._candy_stage and not self._candy_stage._candy_dirty:
            self._candy_stage._candy_queue_sync()

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
        tasks.append(('modify', (self._candy_id, attributes)))
        self._candy_dirty = False

    @property
    def parent(self):
        return self._candy_parent_obj

    @parent.setter
    def parent(self, parent):
        if not self in Widget._candy_sync_reparent:
            self._candy_queue_sync()
            if self._candy_parent_obj:
                self._candy_parent_obj.children.remove(self)
        self._candy_parent_obj = kaa.weakref.weakref(parent)
        if not self in Widget._candy_sync_reparent:
            if parent:
                parent.children.append(self)
            Widget._candy_sync_reparent.append(self)
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
