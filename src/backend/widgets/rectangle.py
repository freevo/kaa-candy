import widget

clutter = candy_module('clutter')

class Rectangle(widget.Widget):

    def create(self):
        self.obj = clutter.Rectangle()
        self.obj.set_color(clutter.Color(60, 60, 0, 0xff))
        self.obj.set_size(self.width, self.height)
        self.obj.show()

