from abmatt.kmp.base import Base, ConnectedPointCollection


class CheckPointGroup(ConnectedPointCollection):
    MAGIC = 'CKPH'


class CheckPoint(Base):
    MAGIC = 'CKPT'
    FMT = '4f4B'
    BYTE_LEN = 0x14

    def __init__(self, left_pole=None, right_pole=None, respawn=None, key=0xff,
                 previous=None, next=None):
        self.next = next
        self.previous = previous
        self.key = key
        self.respawn = respawn
        self.right_pole = right_pole if right_pole else [0, 0]
        self.left_pole = left_pole if left_pole else [0, 0]

    def __eq__(self, o):
        return self is o or super().__eq__(o) \
               and self.key == o.key \
               and self.respawn == o.respawn \
               and self.right_pole == o.right_pole\
               and self.left_pole == o.left_pole
