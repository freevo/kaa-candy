import widget

clutter = candy_module('clutter')

class Rectangle(widget.Widget):

    def create(self):
        self.obj = clutter.Rectangle()
        self.obj.show()

    def update(self, modified):
        super(Rectangle, self).update(modified)
        if 'color' in modified:
            self.obj.set_color(clutter.Color(*self.color))

