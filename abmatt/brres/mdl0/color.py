from abmatt.brres.lib.node import Node


class Color(Node):

    def begin(self):
        self.flags = 0
        self.index = 0
        self.count = 0

    def __len__(self):
        return self.count


