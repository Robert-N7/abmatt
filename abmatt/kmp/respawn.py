from abmatt.kmp.base import Base


class Respawn(Base):
    MAGIC = 'JGPT'
    FMT = '6f2H'
    BYTE_LEN = 0x1c

    def __init__(self, position=None, rotation=None, range=0):
        self.range = range
        self.rotation, self.position = self.init_3((rotation, position))

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.range == \
               other.range and \
               self.rotation == other.rotation and \
               self.position == other.position
