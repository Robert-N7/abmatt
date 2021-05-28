from abmatt.kmp.base import Base


class GameObject(Base):
    MAGIC = 'GOBJ'
    FMT = '2H9f10H'
    BYTE_LEN = 0x3c

    def __init__(self, id=0, extended_presence=0, position=None, rotation=None,
                 scale=None, route=None,
                 settings=None, presence=7):
        self.id = id
        self.extended_presence = extended_presence
        self.position, self.rotation, self.scale = self.init_3(
            (position, rotation, scale))
        self.route = route
        self.settings = list(settings) if settings else [0] * 8
        self.presence = presence

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.id == other.id \
               and self.position == other.position \
               and self.rotation == other.rotation and self.scale == other.scale and self.route == other.route \
               and self.presence == other.presence and self.extended_presence == other.extended_presence
