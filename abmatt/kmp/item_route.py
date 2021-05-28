from abmatt.kmp.base import Base, ConnectedPointCollection


class ItemRoute(ConnectedPointCollection):
    MAGIC = 'ITPH'


class ItemRoutePoint(Base):
    MAGIC = 'ITPT'
    FMT = '4f2H'
    BYTE_LEN = 0x14

    def __init__(self, position=None, width=0, settings=None):
        [self.position] = self.init_3((position,))
        self.settings = list(settings) if settings else [0, 0]
        self.width = width

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.position == \
               other.position and self.settings == other.settings \
               and self.width == other.width
