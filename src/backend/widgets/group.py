import widget

clutter = candy_module('clutter')

class Group(widget.Widget):

    def create(self):
        self.obj = clutter.Group()
        self.obj.show()
