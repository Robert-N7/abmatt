from abmatt.kmp.base import Base


class StartPosition(Base):
    MAGIC = 'KTPT'
    FMT = '6f2H'
    BYTE_LEN = 0x1c

    def __init__(self, position=None, rotation=None, player_id=0xffff):
        self.position, self.rotation = self.init_3((position, rotation))
        self.player_id = player_id

    def __eq__(self, other):
        return other is self or \
               other is not None and type(other) == type(self) and \
               self.position == other.position and \
               self.rotation == other.rotation and \
               self.player_id == other.player_id
