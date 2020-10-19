from abmatt.brres.mdl0.point import Point

XY_POSITION = 0
XYZ_POSITION = 1


class Vertex(Point):
    """ Vertex class for storing vertices data """

    @property
    def point_width(self):
        return self.comp_count + 2

    @property
    def default_comp_count(self):
        return XYZ_POSITION

    @staticmethod
    def comp_count_from_width(width):
        if width == 3:
            return XYZ_POSITION
        elif width == 2:
            return XY_POSITION
        else:
            raise ValueError('Vertex has no comp_count of width {}'.format(width))

    def __str__(self):
        return 'Vertex {} id:{} xyz:{} format:{} divisor:{} stride:{} count:{}'.format(self.name, self.index,
                                                                                       self.comp_count,
                                                                                       self.format, self.divisor,
                                                                                       self.stride, self.count)

