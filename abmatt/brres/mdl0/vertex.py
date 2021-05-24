import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres.mdl0.point import Point

XY_POSITION = 0
XYZ_POSITION = 1


class Vertex(Point):
    __MAX_COORD = 131071
    """ Vertex class for storing vertices data """

    def __deepcopy__(self, memodict=None):
        copy = Vertex(self.name, None)
        return copy.paste(self)

    def check_vertices(self, linked_bone):
        if min(linked_bone.scale) >= 0.9999 and np.allclose(linked_bone.rotation, 0.0):  # only checks if not scaled down and not rotated
            # Check Y value
            if self.parent.name == 'course' and self.minimum[1] + linked_bone.translation[1] < 0:
                AutoFix.warn('Vertex {} minimum y below axis {}'.format(self.name, self.minimum[1]))
            if self.parent.name != 'vrcorn':
                for x in self.minimum:
                    if abs(x) > self.__MAX_COORD:
                        AutoFix.warn(
                            'Vertex {} extreme coordinate {}, (ignore this warning for non-drivable surfaces)'.format(
                                self.name, x))
                for x in self.maximum:
                    if x > self.__MAX_COORD:
                        AutoFix.warn(
                            'Vertex {} extreme coordinate {}, (ignore this warning for non-drivable surfaces)'.format(
                                self.name, x))

    @property
    def point_width(self):
        return self.comp_count + 2

    @property
    def default_point_width(self):
        return 3

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

