from abmatt.kmp.base import Base


class Area(Base):
    MAGIC = 'AREA'
    FMT = '4B9f2H2BH'
    BYTE_LEN = 0x30

    def __init__(self, shape=0, area_type=0, camera=None, priority=0,
                 position=None, rotation=None, scale=None,
                 settings=None, route=None, enemy_point_id=-1):
        self.priority = priority
        self.enemy_point_id = enemy_point_id
        self.settings = settings if settings else [0, 0]
        self.scale, self.rotation, self.position = self.init_3((scale, rotation, position))
        self.camera = camera
        self.area_type = area_type
        self.shape = shape
        self.route = route

    def __eq__(self, other):
        return self is other or \
               super().__eq__(other) and self.priority == other.priority \
               and self.enemy_point_id == other.enemy_point_id and self.settings == other.settings \
               and self.scale == other.scale and self.rotation == other.rotation and self.position == other.position \
               and self.camera == other.camera and self.area_type == other.area_type and self.shape == other.shape \
               and self.route == other.route
