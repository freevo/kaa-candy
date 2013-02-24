# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# modifier.py - Modifier for the XML Parser and Templates
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

__all__ = [ 'Modifier', 'Properties', 'Eventhandler', 'Dependency' ]

# python imports
import logging

# kaa imports
import kaa

# get logging object
log = logging.getLogger('kaa.candy')

class Modifier(object):
    """
    Modifier base class for classes that change widgets on creation by
    templates. In the XML file they are added as subnode to the widget
    to change. Examples are Properties and ReflectionModifier.
    """

    class __metaclass__(type):
        def __new__(meta, name, bases, attrs):
            cls = type.__new__(meta, name, bases, attrs)
            if 'candyxml_name' in attrs.keys():
                if cls.candyxml_name in Modifier._candyxml_modifier:
                    raise RuntimeError('%s already defined' % cls.candyxml_name)
                Modifier._candyxml_modifier[cls.candyxml_name] = cls
            return cls

    _candyxml_modifier = {}

    def modify(self, widget):
        """
        Modify the given widget.
        @param widget: widget to modify
        @returns: changed widget (may be the same)
        """
        raise NotImplementedError

    @classmethod
    def candyxml_create(cls, element):
        """
        Create the modifier for the given element.

        @note: do not call this function from inheriting functions. The name
            is the same but the logic is different. This functions calls the
            implementation variant, not the other way around.
        """
        cls = Modifier._candyxml_modifier.get(element.node)
        if cls is None:
            return cls
        return cls.candyxml_create(element)


class Properties(dict, Modifier):
    """
    Properties class to apply the given properties to a widget. This is a
    dictionary for clutter functions to call after the widget is created.
    """

    #: candyxml name
    candyxml_name = 'properties'

    def modify(self, widget):
        """
        Apply to the given widget.

        @param widget: a kaa.candy.Widget
        """
        for key, value in self.items():
            setattr(widget, key.replace('-', '_'), value)
        return widget

    @classmethod
    def candyxml_create(cls, element):
        """
        Parse the candyxml element and create a Properties object::

          <widget>
            <properties key=value key=value/>
          </widget>
        """
        properties = cls()
        for key, value in element.attributes():
            if key in ('opacity', 'depth', 'scale_x', 'scale_y'):
                value = int(value)
            elif key in ('rotation','xrotation','yrotation','zrotation'):
                value = float(value)
            elif key in ('xalign', 'yalign'):
                value = value.lower()
            elif key in ('keep_aspect',):
                value = value.lower() in ('yes', 'true')
            elif key in ('anchor_point', ):
                value = [ int(x) for x in value.split(',') ]
            properties[key] = value
        return properties


class Eventhandler(dict, Modifier):
    """
    Eventhandler class to apply the given events to a widget.
    """

    #: candyxml name
    candyxml_name = 'event'
    signatures = {
        'replace': 'prev, next',
        'create': 'widget',
    }
    def modify(self, widget):
        """
        Apply to the given widget.

        @param widget: a kaa.candy.Widget
        """
        widget._candy_events.update(self)
        return widget

    @classmethod
    def candyxml_create(cls, element):
        """
        Parse the candyxml element and create an Eventhandler object::

          <widget>
            <event name=value script=value/>
          </widget>
        """
        obj = cls()
        for event in ('%s-%s' % (element.parent.node, element.name), element.name):
            signature = cls.signatures.get(event, None)
            if signature:
                break
        else:
            raise RuntimeError('unable to parse event %s-%s' % (element.parent.node, element.name))
        if element.content.strip():
            func = 'def func(%s):\n' % signature
            if element.content.find('yield') >= 0:
                func = '@kaa.coroutine()\n' + func
            if element.content.strip().find('\n') == -1:
                func += '    '
            func += element.content.rstrip().lstrip('\n') + '\n'
            try:
                exec(func)
                obj[event] = func
                return obj
            except Exception, e:
                log.exception('unable to parse event')
        scripts = element.candyxml.scripts
        obj[event] = scripts[element.script]
        return obj


class Dependency(list, Modifier):
    """
    Dependency class to add the given dependencies to a widget forcing
    a replace when the context changes.
    """

    #: candyxml name
    candyxml_name = 'replace-on-context-change'

    eventhandler = None

    def modify(self, widget):
        """
        Apply to the given widget.

        @param widget: a kaa.candy.Widget
        """
        widget.add_dependencies(*self)
        if self.eventhandler:
            return self.eventhandler.modify(widget)
        return widget

    @classmethod
    def candyxml_create(cls, element):
        """
        Parse the candyxml element and create a Dependency object::

          <widget>
            <replace-on-context-change key="var1 var2"/>
          </widget>
        """
        obj = cls()
        dependency=(element.key or element.keys or '').strip().split(' ')
        while '' in dependency:
            dependency.remove('')
        obj.extend(dependency)
        if element.script or element.content:
            element.name = 'replace'
            obj.eventhandler = Eventhandler.candyxml_create(element)
        return obj
