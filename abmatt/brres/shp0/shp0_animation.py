from abmatt.lib.node import Node


class Shp0KeyFrameList:
    def __init__(self, id):
        self.frames = []
        self.id = id

    def __eq__(self, other):
        return self.id == other.id and self.frames == other.frames

    class Shp0KeyFrame:
        def __init__(self, frame_id, value, delta):
            self.frame_id = frame_id
            self.value = value
            self.delta = delta

        def __eq__(self, other):
            return self.frame_id == other.frame_id and self.value == other.value and self.delta == other.delta


class Shp0Animation(Node):
    """A single animation entry in the file"""
    def __init__(self, name, parent):
        # for modifying, need to add framecount / texture references .. etc
        self.entries = []
        super().__init__(name, parent)

    def __eq__(self, other):
        return super().__eq__(other) and self.entries == other.entries