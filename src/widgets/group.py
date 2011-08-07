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
        self.__intrinsic_size = None

    def __del__(self):
        del self.children
        super(Group, self).__del__()

    def __sync__(self, tasks):
        super(Group, self).__sync__(tasks)
        for child in self.children:
            child.__sync__(tasks)

    def add(self, *widgets):
        """
        Add widgets to the group.
        """
        for widget in widgets:
            widget.parent = self

    def calculate_variable_geometry(self, size):
        """
        Calculate variable geometry for given percentage values
        """
        super(Group, self).calculate_variable_geometry(size)
        if not self._candy_geometry_dirty: # FIXME: that line is not correct!
            return
        size = self.width, self.height
        children_width = children_height = 0
        for child in self.children:
            if child.passive:
                continue
            child.calculate_variable_geometry(size)
            intrinsic_size = child.intrinsic_size
            children_width = max(children_width, child.x + intrinsic_size[0])
            children_height = max(children_height, child.y + intrinsic_size[1])
        self.__intrinsic_size = children_width, children_height
        # now use that calculated size to set the geometry for the
        # passive children
        for child in self.children:
            if child.passive:
                child.calculate_variable_geometry(self.__intrinsic_size)

    @property
    def intrinsic_size(self):
        return self.__intrinsic_size or (self.width, self.height)

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
