from abmatt.brres.mdl0.point import Point

TYPE_NORMAL = 0
TYPE_NORMAL_BINORMAL_TANGENT = 1
TYPE_NORMAL_OR_BINORMAL_OR_TANGENT = 2


class Normal(Point):
    def __deepcopy__(self, memodict=None):
        copy = Normal(self.name, None)
        return copy.paste(self)

    def __hash__(self):
        return super().__hash__()

    @property
    def point_width(self):
        if self.comp_count == TYPE_NORMAL_BINORMAL_TANGENT:
            return 9
        return 3

    @property
    def default_point_width(self):
        return 3

    @property
    def default_comp_count(self):
        return TYPE_NORMAL

    @staticmethod
    def comp_count_from_width(width):
        if width == 9:
            return TYPE_NORMAL_BINORMAL_TANGENT
        elif width == 3:
            return TYPE_NORMAL
        else:
            raise ValueError('Normal has no comp_count of width {}'.format(width))
