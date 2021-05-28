from abmatt.kmp.base import Base


class EndPosition(Base):
    MAGIC = 'MSPT'
    FMT = '6f2H'
    BYTE_LEN = 0x1c

    def __init__(self, position=None, rotation=None, unknown=0):
        self.unknown = unknown
        self.rotation = rotation if rotation else [0, 0, 0]
        self.position = position if position else [0, 0, 0]

    def __eq__(self, other):
        return self is other or\
                super().__eq__(other) and self.position == other.position \
               and self.rotation == other.rotation \
               and self.unknown == other.unknown
