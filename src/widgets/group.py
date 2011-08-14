__all__ = [ 'AbstractGroup', 'Group' ]

import widget
from .. import core

class AbstractGroup(widget.Widget):

    candy_backend = 'candy.Group'
    fixed_size = False

    def __init__(self, pos=None, size=None, context=None):
        super(AbstractGroup, self).__init__(pos, size, context)
        self.children = []

    def __del__(self):
        del self.children
        super(AbstractGroup, self).__del__()

    def __sync__(self, tasks):
        super(AbstractGroup, self).__sync__(tasks)
        for child in self.children:
            child.__sync__(tasks)
        return True

    def prepare_sync(self):
        if not super(AbstractGroup, self).prepare_sync():
            return False
        for child in self.children:
            child.prepare_sync()
        return True

    def context_sync(self):
        context = self.context
        for child in self.children:
            if child.context_sensitive:
                child.context = context

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

    def calculate_intrinsic_size(self, size):
        """
        Calculate intrinsic size based on the parent's size
        """
        super(AbstractGroup, self).calculate_intrinsic_size(size)
        if self.fixed_size:
            return self.width, self.height
        size = self.width, self.height
        children_width = children_height = 0
        for child in self.children:
            if child.passive:
                continue
            intrinsic_size = child.calculate_intrinsic_size(size)
            children_width = max(children_width, child.x + intrinsic_size[0])
            children_height = max(children_height, child.y + intrinsic_size[1])
        self.intrinsic_size = children_width, children_height
        # now use that calculated size to set the geometry for the
        # passive children
        for child in self.children:
            if child.passive:
                child.calculate_intrinsic_size(self.intrinsic_size)
        return self.intrinsic_size

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
            if isinstance(child, Group):
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


class Group(AbstractGroup):

    candyxml_name = 'group'
    context_sensitive = True

    def __init__(self, pos=None, size=None, widgets=[], dependency=None, context=None):
        super(Group, self).__init__(pos, size, context)
        self.children = []
        for widget in widgets:
            if core.is_template(widget):
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
        dependency=(element.depends or '').split(' ')
        while '' in dependency:
            dependency.remove('')
        parameter = super(Group, cls).candyxml_parse(element).update(dependency=dependency)
        widgets = []
        for child in element:
            widget = child.xmlcreate()
            if not widget:
                log.error('unable to parse %s', child.node)
            else:
                widgets.append(widget)
        return parameter.update(widgets=widgets)
