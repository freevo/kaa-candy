import clutter

class Stage(object):

    def create(self):
        """
        Create the clutter stage object
        """
        self.obj = clutter.Stage()

    def init(self, size, group):
        """
        Set the size and the base group
        """
        self.group = group
        self.obj.set_size(*size)
        self.obj.set_color(clutter.Color(0, 0, 0, 0xff))
        self.obj.add(group.obj)
        self.obj.show()

    def scale(self, factor):
        """
        Scale the stage and the core group object
        """
        self.group.obj.set_scale(*factor)
