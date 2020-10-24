class Shp0KeyFrameList:
    def __init__(self, id):
        self.frames = []
        self.id = id

    class Shp0KeyFrame:
        def __init__(self, frame_id, value, delta):
            self.frame_id = frame_id
            self.value = value
            self.delta = delta


class Shp0Animation:
    """A single animation entry in the file"""
    def __init__(self, name):
        # for modifying, need to add framecount / texture references .. etc
        self.name = name
        self.entries = []

