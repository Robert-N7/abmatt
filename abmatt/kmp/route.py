from abmatt.kmp.base import Base, PointCollection


class Route(PointCollection):
    MAGIC = 'POTI'
    FMT = 'H2B'
    BYTE_LEN = 4

    def __init__(self, points=None, settings=None):
        super().__init__(points)
        self.settings = settings if settings else [0] * 2

    def __eq__(self, other):
        return other is self or \
               super().__eq__(other) and self.settings == \
               other.settings and self.points == other.points


class RoutePoint(Base):
    FMT = '3f2H'
    BYTE_LEN = 0x10

    def __init__(self, position=None, speed=0, setting=0):
        [self.position] = self.init_3((position,))
        self.speed = speed
        self.setting = setting

    def __eq__(self, other):
        return other is self or \
               super().__eq__(other) and self.position == other.position \
               and self.speed == other.speed and self.setting == other.setting
