# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# group.py - group widget containing other widgets
# -----------------------------------------------------------------------------
# $Id:$
#
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

__all__ = [ 'AbstractGroup', 'Group', 'ConditionGroup' ]

# python imports
import logging

# kaa imports
import kaa

# kaa.candy imports
from widget import Widget
from .. import is_template

# get logging object
log = logging.getLogger('kaa.candy')

class AbstractGroup(Widget):
    """
    A simple group of widgets. This class has no XML parser function
    and therefore, may be a better base class for widgets holding
    children.
    """
    candy_backend = 'candy.Group'
    attributes = [ 'clip' ]

    clip = None

    def __init__(self, pos=None, size=None, context=None):
        super(AbstractGroup, self).__init__(pos, size, context)
        self.children = []

    def __sync__(self, tasks):
        """
        Internal function to add the changes to the list of tasks for
        the backend.
        """
        super(AbstractGroup, self).__sync__(tasks)
        for child in self.children:
            child.__sync__(tasks)
        return True

    def queue_rendering(self):
        """
        Queue sync for layout changes
        """
        super(AbstractGroup, self).queue_rendering()
        # Note: changing one widget will mark all anchestors dirty to
        # force the __sync__ method to call the widget. On the other
        # side, marking an AbstractGroup dirty will also mark all
        # variable sized children. Therefore, changing one widget may
        # result in a complete re-checking all widgets on sync. This
        # is a stupid and unneccessary task, but keeping all
        # dependencies in account is very complex and maybe not worth
        # it. So we mark everything dirty, no big deal. The sync
        # method will only sync what really changed and by this we
        # have the overhead in the main app and not the backend.
        for child in self.children:
            if child.variable_size and not child._candy_dirty:
                child.queue_rendering()

    def sync_context(self):
        """
        Adjust to a new context
        """
        context = self.context
        for child in self.children[:]:
            if child.freeze_context:
                continue
            if not child.supports_context(context):
                # FIXME: put new child at the same position in the
                # stack as the old one
                new = child.__template__(context=context)
                self.replace(child, new)
            else:
                child.context = context

    def sync_layout(self, size):
        """
        Sync layout changes and calculate intrinsic size based on the
        parent's size.
        """
        super(AbstractGroup, self).sync_layout(size)
        children_width = children_height = 0
        for child in self.children:
            intrinsic_size = child.sync_layout(self.size)
            if child.reference_x != 'parent':
                # ignore this child and calculate this later when we
                # know more about the children
                pass
            elif child.xalign == Widget.ALIGN_SHRINK:
                # auto shrink, use intrinsic size
                children_width = max(children_width, child.x + child.intrinsic_size[0])
            else:
                # use defined width
                children_width = max(children_width, child.x + child.width)
            if child.reference_y != 'parent':
                # ignore this child and calculate this later when we
                # know more about the children
                pass
            elif child.yalign == Widget.ALIGN_SHRINK:
                # auto shrink, use intrinsic size
                children_height = max(children_height, child.y + child.intrinsic_size[1])
            else:
                # use defined height
                children_height = max(children_height, child.y + child.height)
        self.intrinsic_size = children_width, children_height
        # now use that calculated size to set the geometry for the
        # children with their size based on the siblings.
        for child in self.children:
            if child.reference_x == 'parent' and child.reference_y == 'parent':
                continue
            width = children_width if child.reference_x != 'parent' else self.size[0]
            height = children_height if child.reference_y != 'parent' else self.size[1]
            child.sync_layout((width, height))

    def sync_prepare(self):
        """
        Prepare widget for the next sync with the backend
        """
        if not super(AbstractGroup, self).sync_prepare():
            return False
        for child in self.children:
            child.sync_prepare()
        return True

    def get_widget(self, name):
        """
        Get child element with the given name. For group children this
        function will search recursive.

        @param name: name of the child
        @returns: widget or None
        """
        for child in self.children:
            if child.name == name:
                return child
            if isinstance(child, AbstractGroup):
                result = child.get_widget(name)
                if result is not None:
                    return result
        return None

    def add(self, *widgets):
        """
        Add widgets to the group.
        """
        for widget in widgets:
            widget.parent = self

    def remove(self, *widgets):
        """
        Remove widgets from the group.
        """
        for widget in widgets:
            widget.parent = None

    @kaa.coroutine()
    def replace(self, child, replacement):
        """
        Replace the given child with the replacement. Emit the child's
        replace event.
        """
        replacement.parent = self
        child.freeze_context = True
        try:
            replacing = child.emit('replace', child, replacement)
            if isinstance(replacing, kaa.InProgress):
                yield replacing
        except Exception, e:
            log.exception('replacing error')
        child.freeze_context = False
        child.parent = None

    def clear(self):
        """
        Clear the group by removing all children
        """
        for widget in self.children[:]:
            widget.parent = None



class Group(AbstractGroup):
    """
    Group widget with XML support
    """

    candyxml_name = 'group'

    def __init__(self, pos=None, size=None, widgets=[], context=None):
        super(Group, self).__init__(pos, size, context)
        for widget in widgets:
            if is_template(widget):
                widget = widget(context)
            self.add(widget)

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget. Example::
            <group x='10' y='0' width='200' height=100'>
                <child_widget1/>
                <child_widget2/>
            </group>
        """
        widgets = []
        parameter = super(Group, cls).candyxml_parse(element).update(widgets=widgets)
        for child in element:
            try:
                widget = child.xmlcreate()
            except Exception, e:
                log.error('unable to parse %s: %s', child.node, e)
                continue
            if not widget:
                log.error('unable to parse %s', child.node)
                continue
            widgets.append(widget)
        return parameter


class ConditionGroup(AbstractGroup):
    """
    Group widget switch/case with XML support
    """

    candyxml_name = 'group'
    candyxml_style = 'condition'

    def __init__(self, pos=None, size=None, conditions=[], context=None):
        super(ConditionGroup, self).__init__(pos, size, context)
        for pos, (condition, value, widgets) in enumerate(conditions):
            if isinstance(condition, (str, unicode)):
                condition = self.context.get(condition)
            if value:
                condition = not cmp(str(condition).lower(), str(value).lower())
            if condition:
                for widget in widgets:
                    if is_template(widget):
                        widget = widget(context)
                    self.add(widget)
                break
        else:
            pos = -1
        self.__condition = pos, conditions

    def supports_context(self, context):
        """
        Check if the widget is capable of the given context based on its
        dependencies.
        """
        if not super(ConditionGroup, self).supports_context(context):
            return False
        old, conditions = self.__condition
        for pos, (condition, value, widgets) in enumerate(conditions):
            if isinstance(condition, (str, unicode)):
                condition = context.get(condition)
            if value:
                condition = not cmp(str(condition).lower(), str(value).lower())
            if condition:
                return pos == old
        return False

    @classmethod
    def candyxml_parse(cls, element):
        """
        Parse the candyxml element for parameter to create the widget.
        """
        conditions = []
        parameter = super(ConditionGroup, cls).candyxml_parse(element).update(conditions=conditions)
        for c in element:
            widgets = []
            for child in c:
                try:
                    widget = child.xmlcreate()
                except Exception, e:
                    log.error('unable to parse %s: %s', child.node, e)
                    continue
                if not widget:
                    log.error('unable to parse %s', child.node)
                    continue
                widgets.append(widget)
            conditions.append((c.condition or True, c.value, widgets))
        return parameter
