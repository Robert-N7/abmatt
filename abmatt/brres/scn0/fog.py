from abmatt.lib.node import Node


class Fog(Node):
    def begin(self):
        self.node_id = 0
        self.real_id = 0
        self.flags = 0
        self.type = 0
        self.start = 0.0
        self.end = 0.0
        self.color = [0, 0, 0, 0]

    def __eq__(self, other):
        return super().__eq__(other) and self.node_id == other.node_id and self.real_id == other.real_id \
               and self.flags == other.flags and self.type == other.type and self.start == other.start \
               and self.end == other.end and self.color == other.color
