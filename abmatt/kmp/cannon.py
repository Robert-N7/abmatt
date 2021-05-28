from abmatt.kmp.base import Base


class Cannon(Base):
    MAGIC = 'CNPT'
    BYTE_LEN = 0x1c
    FMT = '6f2H'

    def __init__(self, position=None, rotation=None, shoot_effect=0):
        self.shoot_effect = shoot_effect
        self.rotation, self.position = self.init_3((rotation, position))

    def __eq__(self, o):
        return self is o or super().__eq__(o) \
               and self.position == o.position and self.rotation == o.rotation