# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - Core Widgets and Template
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# kaa-candy - Third generation Canvas System using Clutter as backend
# Copyright (C) 2008 Dirk Meyer, Jason Tackaberry
#
# First Version: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------

__all__ = [ 'Widget', 'Group', 'Texture', 'CairoTexture']

# python imports
import logging
import time
from copy import deepcopy

# clutter imports
import pango
import cairo

# kaa imports
import kaa.imlib2
from kaa.utils import property

# kaa.candy imports
from .. import candyxml, animation, Modifier, backend

# get logging object
log = logging.getLogger('kaa.candy')

class XMLDict(dict):
    """
    XML parser dict helper class.
    """
    def update(self, **kwargs):
        super(XMLDict, self).update(**kwargs)
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
        @param cls: widget class
        @param kwargs: keyword arguments for cls.__init__
        """
        self._cls = cls
        self._modifier = kwargs.pop('modifier', [])
        self._kwargs = kwargs
        self.userdata = {}

    def __call__(self, context=None):
        """
        Create the widget with the given context and override some
        constructor arguments.
        @param context: context to create the widget in
        @returns: widget object
        """
        if self._cls.context_sensitive:
            self._kwargs['context'] = context
        try:
            widget = self._cls(**self._kwargs)
        except TypeError, e:
            log.exception('error creating %s%s', self._cls, self._kwargs.keys())
            return None
        for modifier in self._modifier:
            widget = modifier.modify(widget)
        return widget

    def get_attribute(self, attr):
        """
        Get the value for the attribute for object creation.
        @param attr: attribute name for cls.__init__
        @returns: attribute value or None if not set
        """
        return self._kwargs.get(attr)

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
        @param element: kaa.candy.candyxml.Element with widget information
        @returns: Template object
        """
        modifier = []
        for subelement in element.get_children():
            mod = Modifier.candyxml_create(subelement)
            if mod:
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
    """
    Basic widget. All widgets from the backend must inherit from it.
    @group Context Management: set_context, get_context, try_context, eval_context
    @group Animations: animate, stop_animations, set_animation
    @cvar context_sensitive: class variable for inherting class if the class
        depends on the context.
    """

    #: set if the object reacts on set_context
    context_sensitive = False

    #: template for object creation
    __template__ = Template

    # some default values
    __need_update = True
    __need_rendering = True
    __need_layout = True
    # properties
    __parent = None
    __anchor = None
    __x = 0
    __y = 0
    __width = 0
    __height = 0

    # misc
    name = None
    _obj = None

    def __init__(self, pos=None, size=None, context=None):
        """
        Basic widget constructor.
        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget or None.
        @param context: the context the widget is created in
        """
        if size is not None:
            self.__width  = size[0] or 0
            self.__height = size[1] or 0
        if pos is not None:
            self.__x, self.__y = pos
        self.__depends = {}
        self.__context = context or {}
        self.userdata = {}
        # DEPRECATED ANIMATION SUPPORT
        # # animations running created by self.animate()
        # self._running_animations = {}
        # self.__animations = {}

    def get_context(self, key=None):
        """
        Get the context the widget is in.
        @param key: if key is not None return only the value for key
            from the context
        @returns: context dict or value for the key
        """
        if key is None:
            return self.__context
        return self.__context.get(key)

    def set_context(self, context):
        """
        Set a new context.
        @param context: dict of context key,value pairs
        """
        self.__context = context

    def try_context(self, context):
        """
        Check if the widget is capable of the given context based on its
        dependencies. If it is possible set the context.
        @param context: context dict
        @returns: False if the widget can not handle the context or True
        """
        if self.__depends:
            try:
                for var, value in self.__depends.items():
                    if value != repr(eval(var, context)):
                        return False
            except AttributeError:
                return False
        self.set_context(context)
        return True

    def eval_context(self, var, default=None, context=None, depends=True):
        """
        Evaluate the context for the given variable. This function is used by
        widgets to evaluate the context and set their dependencies. It should
        not be called from outside the widget.
        @param var: variable name to eval
        @param default: default return value if var is not found
        @param context: context to search, default is the context set on init
            or by set_context.
        @param depends: if set the true the variable and the value will be stored
            as dependency and try_context will return False if the value changes.
        """
        if var.startswith('$'):
            # strip prefix for variables if set
            var = var[1:]
        context = context or self.__context
        try:
            # try the variable as it is
            value = eval(var, context)
        except AttributeError:
            # not found. Maybe it is an object with a get method.
            # foo.bar.buz could be foo.bar.get('buz')
            pos = var.rfind('.')
            if pos == -1:
                # no dot found, too bad
                log.error('unable to evaluate %s', var)
                return default
            try:
                var = '%s.get("%s")' % (var[:pos], var[pos+1:])
                value = eval(var, context)
                if value is None:
                    value = default
            except AttributeError:
                log.error('unable to evaluate %s', var)
                return default
        if depends:
            self.__depends[var] = repr(value)
        return value

    def destroy(self):
        """
        Destroy the widget. This function _must_ be called when animations
        running in the widget to stop them first.
        """
        # DEPRECATED ANIMATION SUPPORT
        # for animation in self._running_animations.values():
        #     animation._clutter_stop()
        if self.__parent is not None:
            self.__parent._remove_child(self)
        self.__parent = None
        self._obj = None

    # DEPRECATED ANIMATION SUPPORT
    # def set_animation(self, name, animations):
    #     """
    #     Set additional animations for object.animate()
    #     @param animations: dict with key,Animation
    #     """
    #     self.__animations[name] = animations

    # def animate(self, name, *args, **kwargs):
    #     """
    #     Animate the object with the given animation. The animations are defined
    #     by C{set_animation}, the candyxml definition or the basic animation
    #     classes in kaa.candy.animation. Calling this function is thread-safe.
    #     @param name: name of the animation used by C{set_animation} or
    #         kaa.candy.animations
    #     """
    #     # FIXME: rewrite animation code
    #     if name in self.__animations:
    #         return self.__animations[name](self, *args, **kwargs)
    #     a = animation.get(name)
    #     if a:
    #         return a(self, *args, **kwargs)
    #     if not name in ('hide', 'show'):
    #         log.error('no animation named %s', name)

    # def stop_animations(self):
    #     """
    #     Stop all running animations for the widget. This function must be called
    #     when a widget is removed from the stage. Calling C{destroy} will also
    #     stop all animations.
    #     """
    #     for animation in self._running_animations.values():
    #         animation._clutter_stop()

    # rendering

    def _require_update(self, rendering=False, layout=False):
        """
        Trigger rendering or layout functions to be called from the
        clutter mainloop.
        """
        if rendering:
            self.__need_rendering = True
        if layout:
            self.__need_layout = True
        self.__need_update = True
        if self.__parent and not self.__parent.__need_update:
            self.__parent._require_update()

    def _candy_update(self):
        """
        Called from the clutter thread to update the widget.
        """
        if not self.__need_update:
            return False
        self.__need_update = False
        if self.__need_rendering:
            self.__need_rendering = False
            self._candy_render()
        if self.__need_layout:
            self.__need_layout = False
            self._candy_layout()
        return True

    def _candy_render(self):
        """
        Render the widget
        """
        raise NotImplemented

    def _candy_layout(self):
        """
        Layout the widget
        """
        if self.__anchor:
            self._obj.set_anchor_point(*self.__anchor)
            self._obj.set_position(
                self.__x + self.__anchor[0], self.__y + self.__anchor[1])
        else:
            self._obj.set_position(self.__x, self.__y)

    # properties

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x
        self._require_update(layout=True)

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y
        self._require_update(layout=True)

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if self._obj is not None:
            # FIXME: support changing the geometry
            raise RuntimeError('unable to update during runtime')
        self.__width = width
        self._require_update(rendering=True, layout=True)

    @property
    def height(self):
        return self.__height

    @height.setter
    def height(self, height):
        if self._obj is not None:
            # FIXME: support changing the geometry
            raise RuntimeError('unable to update during runtime')
        self.__height = height
        self._require_update(rendering=True, layout=True)

    @property
    def anchor_point(self):
        return self.__anchor or (0, 0)

    @anchor_point.setter
    def anchor_point(self, (x, y)):
        self.__anchor = x, y
        self._require_update(layout=True)

    @property
    def parent(self):
        return __parent

    @parent.setter
    def parent(self, parent):
        """
        Set the parent widget.
        @param parent: kaa.candy Group or Stage object
        """
        if self.__parent:
            self.__parent._remove_child(self)
        self.__parent = parent
        self.__parent._add_child(self)


    # candyxml stuff

    @classmethod
    def create_template(cls, **kwargs):
        """
        Create a template for this class.
        @param kwargs: keyword arguments based on the class __init__ function
        """
        return cls.__template__(cls, **kwargs)

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. This function
        must be overwitten by a subclass for the correct parsing. This class
        only parses pos and size::
          <widget x='10' y='20' width='100' height='50'/>
        """
        return XMLDict(pos=element.pos, size=(element.width, element.height))

    @classmethod
    def candyxml_register(cls, style=None):
        """
        Register class to candyxml. This function can only be called
        once when the class is loaded.
        """
        candyxml.register(cls, style)

    # def __del__(self):
    #     print '__del__', self

class Group(Widget):
    """
    Group widget.
    """
    def __init__(self, pos=None, size=None, context=None):
        """
        Simple clutter.Group widget
        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget or None. A clutter.Group
            does not respect the given geometry. If set, the geometry can be
            read with the get_max memeber functions.
        @param context: the context the widget is created in
        """
        super(Group, self).__init__(pos, size, context)
        self.children = []
        self._new_children = []
        self._del_children = []

    def _candy_update(self):
        """
        Called from the clutter thread to update the widget.
        """
        if not super(Group, self)._candy_update():
            return False
        while self._del_children:
            self._obj.remove(self._del_children.pop(0))
        for child in self.children:
            child._candy_update()
        while self._new_children:
            actor = self._new_children.pop(0)._obj
            actor.show()
            self._obj.add(actor)
        return True

    def _candy_render(self):
        """
        Render the widget
        """
        if self._obj is None:
            self._obj = backend.Group()

    def _add_child(self, child):
        """
        Add a child and set it visible.
        @param child: kaa.candy.Widget, NOT a Template
        """
        self._require_update()
        self._new_children.append(child)
        self.children.append(child)

    def _remove_child(self, child):
        self._require_update()
        self.children.remove(child)
        self._del_children.append(child._obj)

    def destroy(self):
        """
        Destroy the group and all children. The object is removed from the
        parant and not usable anymore.
        """
        for child in self.children:
            child.destroy()
        super(Group, self).destroy()


class Texture(Widget):
    """
    Clutter Texture widget.
    """
    def __init__(self, pos=None, size=None, context=None):
        """
        Simple clutter.Texture widget
        @param pos: (x,y) position of the widget or None
        @param size: (width,height) geometry of the widget or None.
        @param context: the context the widget is created in
        """
        super(Texture, self).__init__(pos, size, context)
        self._imagedata = None

    def set_image(self, image):
        if image and not isinstance(image, kaa.imlib2.Image):
            image = kaa.imlib2.Image(image)
        self._imagedata = image
        self._require_update(rendering=True)

    def _candy_render(self):
        """
        Render the widget
        """
        if self._obj is None:
            self._obj = backend.Texture()
            self._obj.set_size(self.width, self.height)
        if not self._imagedata:
            return
        self._obj.set_from_rgb_data(self._imagedata.get_raw_data(), True,
            self._imagedata.width, self._imagedata.height, 1, 4,
            backend.TEXTURE_RGB_FLAG_BGR)


class CairoTexture(Widget):
    """
    Cairo based Texture widget.
    """

    def _candy_render(self):
        """
        Render the widget
        """
        if self._obj is None:
            self._obj = backend.CairoTexture(self.width, self.height)
        else:
            context = self._obj.cairo_create()
            context.set_operator(cairo.OPERATOR_CLEAR)
            context.set_source_rgba(255,255,255,255)
            context.paint()
            del context
