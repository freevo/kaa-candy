import widget

class Rectangle(widget.Widget):

    def create(self):
        self.obj = self.clutter.Rectangle()
        self.obj.set_color(self.clutter.Color(60, 60, 0, 0xff))
        self.obj.set_size(self.width, self.height)
        self.obj.show()

