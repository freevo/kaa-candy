import widget

class Group(widget.Widget):

    def create(self):
        self.obj = self.clutter.Group()
        self.obj.show()
