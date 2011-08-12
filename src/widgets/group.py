__all__ = [ 'Group' ]

import widget
from ..core import is_template

class Group(widget.Widget):
    candy_backend = 'candy.Group'

    candyxml_name = 'group'
    context_sensitive = True

    def __init__(self, pos=None, size=None, widgets=[], dependency=None, context=None):
        super(Group, self).__init__(pos, size, context)
        self.children = []
        for widget in widgets:
            if is_template(widget):
                template = widget
                widget = template(context)
            self.add(widget)

    def __del__(self):
        del self.children
        super(Group, self).__del__()

    def __sync__(self, tasks):
        super(Group, self).__sync__(tasks)
        for child in self.children:
            child.__sync__(tasks)
        return True

    def queue_rendering(self):
        """
        Queue sync for layout changes
        """
        super(Group, self).queue_rendering()
        # Note: changing one widget will mark all anchestors dirty to
        # force the __sync__ method to call the widget. On the other
        # side, marking a Group dirty will also mark all variable
        # sized children. Therefore, changing one widget may result in
        # a complete re-checking all widgets on sync. This is a stupid
        # and unneccessary task, but keeping all dependencies in
        # account is very complex and maybe not worth it. So we mark
        # everything dirty, no big deal. The sync method will only
        # sync what really changed and by this we have the overhead in
        # the main app and not the backend.
        for child in self.children:
            if child.variable_size and not child._candy_dirty:
                child.queue_rendering()

    def calculate_intrinsic_size(self, size):
        """
        Calculate intrinsic size based on the parent's size
        """
        super(Group, self).calculate_intrinsic_size(size)
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

    def add(self, *widgets):
        """
        Add widgets to the group.
        """
        for widget in widgets:
            widget.parent = self

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
