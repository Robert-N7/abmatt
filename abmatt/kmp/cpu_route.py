from abmatt.kmp.base import Base, ConnectedPointCollection


class CpuRoute(ConnectedPointCollection):
    MAGIC = 'ENPH'


class CpuRoutePoint(Base):
    MAGIC = 'ENPT'
    FMT = '4fH2B'
    BYTE_LEN = 0x14

    def __init__(self, position=None, width=0, settings=None):
        [self.position] = self.init_3((position,))
        self.width = width
        self.settings = settings if settings else [0] * 3

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.position == other.position \
               and self.width == other.width \
               and self.settings == other.settings