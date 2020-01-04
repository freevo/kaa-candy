# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# template.py - Template for creating a widget
# -----------------------------------------------------------------------------
# kaa-candy - Fourth generation Canvas System using Clutter as backend
# Copyright (C) 2011 Dirk Meyer
#
# First Version: Dirk Meyer <https://github.com/Dischi>
# Maintainer:    Dirk Meyer <https://github.com/Dischi>
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

__all__ = [ 'is_template', 'Template' ]

# python imports
import logging
import traceback

# kaa.candy imports
from core import Context
from modifier import Modifier
from candyxml import get_class

# get logging object
log = logging.getLogger('kaa.candy')


def is_template(obj):
    """
    Returns True if the given object is a kaa.candy template class. This function
    is needed to check if a given widget is a real clutter widget or only a template
    for creating one.
    """
    return isinstance(obj, Template)


class Template(object):
    """
    Template to create a widget on demand. All XML parsers will create such an
    object to parse everything at once.
    """

    def __init__(self, cls, name, **kwargs):
        """
        Create a template for the given class

        :param cls: widget class
        :param kwargs: keyword arguments for cls.__init__
        """
        self._cls = cls
        self._modifier = kwargs.pop('modifier', [])
        self._kwargs = kwargs
        self.name = name

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
        args['context'] = context
        try:
            widget = self._cls(**args)
            widget.__template__ = self
            widget.name = self.name
        except Exception, e:
            log.exception('unable to create widget %s', self._cls)
            raise RuntimeError('unable to create %s%s: %s' % (self._cls, args.keys(), e))
        for modifier in self._modifier:
            widget = modifier.modify(widget)
        return widget

    def __repr__(self):
        return '<kaa.candy.Template for %s>' % self._cls

    @classmethod
    def candyxml_get_class(cls, element):
        """
        Get the class for the candyxml element. This function may be overwritten
        by inheriting classes and should not be called from outside such a class.
        """
        return get_class(element.node, element.style)

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
        template = cls(widget, name=kwargs.candyname, **kwargs)
        return template
