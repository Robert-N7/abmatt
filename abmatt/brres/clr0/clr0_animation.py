from abmatt.brres.lib.node import Node


class Clr0Animation(Node):

    def __init__(self, name, parent):
        self.name = name
        self.framecount = parent.framecount
        self.loop = parent.loop
        self.flags = [False] * 16
        self.is_constant = [False] * 16
        self.entry_masks = []
        self.entries = []  # can be fixed (if constant) otherwise key frame list
        super().__init__(name, parent)

    def __eq__(self, other):
        return super().__eq__(other) and self.framecount == other.framecount and self.loop == other.loop \
               and self.flags == other.flags and self.is_constant == other.is_constant \
               and self.entry_masks == other.entry_masks and self.entries == other.entries
