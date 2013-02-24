# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# widget.py - base widget class
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Based on various previous attempts to create a canvas system for
# Freevo by Dirk Meyer and Jason Tackaberry.  Please see the file
# AUTHORS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

__all__ = [ 'XMLdict', 'Widget' ]

# Python imports
import os
import sys

# kaa imports
import kaa
import kaa.weakref

# kaa.candy imports
from .. import candyxml
from ..core import Context
from ..template import Template

next_id = 1

NOT_SET = object()

class XMLdict(dict):
    """
    XML parser dict helper class.
    """
    candyname = None
    def update(self, **kwargs):
        super(XMLdict, self).update(**kwargs)
        return self
    def remove(self, *args):
        for arg in args:
            self.pop(arg)
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
    candyxml_name = None
    candyxml_style = None
    candyxml_override = False

    attributes = []
    attribute_types = {}

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
    _candy_import = []
    _candy_backends = {}

    # internal object variables
    _candy_id = None
    _candy_dirty = True
    _candy_stack = None
    stage = None

    class __metaclass__(type):
        def __new__(meta, name, bases, attrs):
            cls = type.__new__(meta, name, bases, attrs)
            if 'candyxml_name' in attrs.keys() or 'candyxml_style' in attrs.keys() \
                    or 'candyxml_override' in attrs.keys():
                candyxml.register(cls)
            backend = cls.candy_backend.split('.')[0]
            if backend != 'candy':
                path = os.path.dirname(sys.modules[cls.__module__].__file__) + '/' + backend
                if not path in cls._candy_backends:
                    dyn = 'dyn%03d' % len(cls._candy_backends.keys())
                    cls._candy_backends[path] = dyn
                    cls._candy_import.append((dyn, path))
                cls.candy_backend = cls._candy_backends[path] + cls.candy_backend[len(backend):]
            return cls

    #: template for object creation
    __template__ = Template

    # widgets with dynamic size depend on the size of the paent or
    # other widgets in a group based on the reference setting.
    # Possible values are 'parent' based on the parents geometry and
    # 'siblings' based on its siblings.
    reference_x = 'parent'
    reference_y = 'parent'

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
    __stage = None

    # attributes
    name = None

    xalign = None
    yalign = None

    opacity = 255
    scale_x = 1
    scale_y = 1
    anchor_point = 0, 0

    visible = True

    # if True, the context will not be updated by the parent
    freeze_context = False

    def __init__(self, pos=None, size=None, context=None):
        self.attributes = self.attributes + ['xalign', 'yalign', 'opacity', 'scale_x', 'scale_y', 'anchor_point', 'visible']
        self._candy_events = {}
        global next_id
        self._candy_id = next_id
        next_id += 1
        self.backend = BackendWrapper(self._candy_id)
        Widget._candy_sync_new.append(self)
        if pos is not None:
            self.x, self.y = pos
        if size is not None:
            self.width, self.height = size
        self.__sync_cache = {}
        self.__context = context or {}
        self.__depends = {}

    def __setattr__(self, attr, value):
        if value and attr in self.attribute_types and not isinstance(value, self.attribute_types[attr]):
            value = self.attribute_types[attr](value)
        super(Widget, self).__setattr__(attr, value)
        if not self._candy_dirty and (attr in self.attributes):
            self.queue_rendering()

    def __del__(self):
        if not hasattr(self, '_candy_id') or not Widget:
            # Python is shutting down, no need to clean anymore -- and
            # not possible.
            return
        Widget._candy_sync_delete.append(self._candy_id)
        if self.__stage and not self.__stage._candy_dirty:
            self.__stage.queue_rendering()

    def emit(self, event, *args):
        """
        Emit the given event
        """
        if event in self._candy_events:
            return self._candy_events[event](*args) or True
        return False

    def __sync__(self, tasks):
        """
        Internal function to add the changes to the list of tasks for
        the backend.
        """
        if not self._candy_dirty:
            return False
        if self._candy_events.get('create'):
            self._candy_events.pop('create')(self)
        (x, y), (width, height) = self.intrinsic_geometry
        # check the position and set a new position on the backend if
        # needed. This does not result in a new rendering.
        attributes = {}
        for (attr, value) in [ ('x', x), ('y', y) ]:
            if self.__sync_cache.get(attr, NOT_SET) != value:
                attributes[attr] = value
        if attributes:
            self.__sync_cache.update(attributes)
            tasks.append(('position', (self._candy_id, x, y)))
        # check all other attributes and this will cause a
        # re-rendering. Even width and height change the widget on the
        # backend.
        attributes = {}
        for attr in self.attributes:
            new_value = getattr(self, attr)
            if self.__sync_cache.get(attr, NOT_SET) != new_value:
                attributes[attr] = new_value
        for (attr, value) in [ ('width', width), ('height', height) ]:
            if self.__sync_cache.get(attr, NOT_SET) != value:
                attributes[attr] = value
        if attributes:
            self.__sync_cache.update(attributes)
            tasks.append(('update', (self._candy_id, attributes)))
        self._candy_dirty = False
        return True

    def queue_rendering(self):
        """
        Queue sync
        """
        self.__intrinsic_size = None
        # if self._candy_dirty:
        #     return True
        self._candy_dirty = True
        parent = self.parent
        if parent:# and not parent._candy_dirty:
            parent.queue_rendering()
        return False

    def sync_context(self):
        """
        Adjust to a new context
        """
        pass

    def sync_layout(self, (width, height)):
        """
        Sync layout changes and calculate intrinsic size based on the
        parent's size.
        """
        if self.__variable_width:
            self.__width = int((width * self.__variable_width) / 100)
        if self.__variable_height:
            self.__height = int((height * self.__variable_height) / 100)
        self.__intrinsic_size = self.__width, self.__height

    def sync_prepare(self):
        """
        Prepare widget for the next sync with the backend
        """
        return self._candy_dirty

    @kaa.coroutine()
    def animate(self, ease, secs, unparent=False, **kwargs):
        args = [item for sublist in kwargs.items() for item in sublist]
        if secs:
            self.backend.animate(ease, secs, *args)
            yield kaa.delay(secs)
            for key, value in kwargs.items():
                self.__sync_cache[key] = value
        for key, value in kwargs.items():
            setattr(self, key, value)
        if unparent:
            self.parent = None

    def add_dependencies(self, *vars):
        """
        Evaluate the context for the given variable and depend on the result

        :param var: variable name to eval
        """
        for var in vars:
            self.__depends[var] = repr(self.__context.get(var))

    def supports_context(self, context):
        """
        Check if the widget is capable of the given context based on its
        dependencies.

        :param context: context dict
        :returns: False if the widget can not handle the context or True
        """
        try:
            for var, value in self.__depends.items():
                if value != repr(context.get(var)):
                    return False
        except AttributeError, e:
            log.error('supports_context: %s', e)
            return False
        return True

    def raise_top(self):
        """
        Raise widget to the top of the stack
        """
        self.backend.raise_top()

    def lower_bottom(self):
        """
        Lower widget to the bottom of the stack
        """
        self.backend.lower_bottom()

    def above_sibling(self, sibling):
        """
        Move the widget above the given sibling
        """
        self.backend.above_sibling('candy:widget:%s' % sibling._candy_id)

    def unparent(self):
        """
        Unparent the widget. Calls widget.parent = None
        """
        self.parent = None

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
        if self.__variable_width and not self.__intrinsic_size and self.parent:
            # start intrinsic size calculations
            self.intrinsic_size
        return self.__width

    @width.setter
    def width(self, width):
        self.__intrinsic_size = None
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
        if self.__variable_height and not self.__intrinsic_size and self.parent:
            # start intrinsic size calculations
            self.intrinsic_size
        return self.__height

    @height.setter
    def height(self, height):
        self.__intrinsic_size = None
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
                self.sync_layout(self.parent.size)
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
        return (x + self.anchor_point[0], y + self.anchor_point[1]), (width, height)

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, parent):
        self._candy_stack = None
        if not self in Widget._candy_sync_reparent:
            self.queue_rendering()
        if self.__parent:
            self.__parent.children.remove(self)
        if parent:
            self.__parent = kaa.weakref.weakref(parent)
            self.__parent.children.append(self)
        else:
            self.__parent = None
        if not self in Widget._candy_sync_reparent:
            if parent:
                parent.queue_rendering()
            Widget._candy_sync_reparent.append(self)
            self.queue_rendering()

    @property
    def stage(self):
        if not self.__stage and self.__parent:
            return self.parent.stage
        return self.__stage

    @stage.setter
    def stage(self, stage):
        if self.__stage:
            raise AttributeError('stage is a read-only variable')
        self.__stage = stage

    @property
    def context(self):
        return self.__context

    @context.setter
    def context(self, context):
        if not isinstance(context, Context):
            context = Context(context)
        self.__context = context
        self.sync_context()

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
        parameter = XMLdict(pos=element.pos, size=(element.width, element.height))
        for child in element[:]:
            if child.use_as:
                widget = child.xmlcreate()
                if not widget:
                    log.error('unable to parse %s', child.node)
                else:
                    parameter[str(child.use_as)] = widget
                element.remove(child)
        parameter.candyname = element.name
        return parameter
