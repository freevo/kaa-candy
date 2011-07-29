__all__ = [ 'Group' ]

import widget
from backend import Group as BackendCls

from ..core import is_template

class Group(widget.Widget):
    BackendCls = BackendCls

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

    def add(self, *widgets):
        """
        Add widgets to the group.
        """
        for widget in widgets:
            # TODO: that should happen in the next line
            self.children.append(widget)
            widget.parent = self

    def _candy_sync(self, tasks):
        super(Group, self)._candy_sync(tasks)
        for child in self.children:
            child._candy_sync(tasks)
        # TODO: check for dirty

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
