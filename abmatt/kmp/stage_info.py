from abmatt.kmp.base import Base


class StageInfo(Base):
    MAGIC = 'STGI'
    FMT = '12B'
    BYTE_LEN = 0xc

    def __init__(self, lap_count=3, pole_position_right=False, narrow=False,
                 lens_flashing=False,
                 flare_color=None, speed_mod=1.0):
        self.speed_mod = speed_mod
        self.flare_color = flare_color if flare_color else [255, 255, 255, 255]
        self.lens_flashing = lens_flashing
        self.narrow = narrow
        self.pole_position_right = pole_position_right
        self.lap_count = lap_count

    def __eq__(self, other):
        return other is self or \
               other is not None and type(other) == type(self) and \
               self.speed_mod == other.speed_mod and \
               self.flare_color == other.flare_color and \
               self.lens_flashing == other.lens_flashing and \
               self.narrow == other.narrow and \
               self.pole_position_right == other.pole_position_right and \
               self.lap_count == other.lap_count
