from abmatt.brres.mdl0.point import Point

COORD_S = 0
COORD_ST = 1


class TexCoord(Point):
    @property
    def point_width(self):
        return self.comp_count + 1

    @staticmethod
    def comp_count_from_width(width):
        if width == 2:
            return COORD_ST
        elif width == 1:
            return COORD_S
        else:
            raise ValueError('UV has no comp_count of width {}'.format(width))

    @property
    def default_comp_count(self):
        return COORD_ST

    def begin(self):
        super(TexCoord, self).begin()

