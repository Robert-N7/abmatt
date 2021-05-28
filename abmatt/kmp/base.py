class Base:
    FMT = None
    BYTE_LEN = None
    MAGIC = None

    @staticmethod
    def init_3(args):
        return [list(x) if x else [0, 0, 0] for x in args]

    def __eq__(self, other):
        return other is not None and type(other) is type(self)


class PointCollection(Base):

    def __init__(self, points=None):
        self.points = points if points is not None else []

    def __len__(self):
        return len(self.points)

    def __getitem__(self, item):
        return self.points[item]

    def __setitem__(self, key, value):
        self.points[key] = value

    def __iter__(self):
        return iter(self.points)

    def __next__(self):
        return next(self.points)


class ConnectedPointCollection(PointCollection):
    FMT = '16B'
    BYTE_LEN = 0x10

    def __init__(self, points=None, settings=None):
        super().__init__(points)
        self.next_groups = []
        self.prev_groups = []
        self.settings = [0, 0] if not settings else settings

    def __eq__(self, o):
        return self is o or super().__eq__(o) \
               and self.points == o.points and self.settings == o.settings
