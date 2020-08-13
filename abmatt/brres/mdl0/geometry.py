from struct import pack

from brres.lib.autofix import AUTO_FIXER
from brres.lib.node import Node
from brres.lib import binfile


class Geometry(Node):

    def encode_data(self, point_collection):
        """Encodes the point collection as geometry data, returns the data width (component count)"""
        self.minimum = point_collection.minimum
        self.maximum = point_collection.maximum
        form, divisor = self.get_format_divisor(point_collection.minimum, point_collection.maximum)
        points = point_collection.points
        self.count = len(points)
        point_width = len(points[0])
        fmt_str = '>'
        if form == 4:
            self.stride = point_width * 4
            fmt_str += '{}f'.format(point_width)
        elif form > 1:
            self.stride = point_width * 2
            t_str = 'H' if form == 2 else 'h'
            fmt_str += str(point_width) + t_str
        else:
            self.stride = point_width
            t_str = 'B' if form == 0 else 'b'
            fmt_str += str(point_width) + t_str
        self.format = form
        self.divisor = divisor
        multiplyBy = 2 ** divisor
        data = bytearray()
        if divisor:
            for x in point_collection.points:
                t = [y * multiplyBy for y in x]
                data.extend(pack(fmt_str, *t))
        else:
            for x in point_collection.points:
                data.extend(pack(fmt_str, *x))
        self.data = data
        return point_width

    @staticmethod
    def get_format_divisor(minimum, maximum):
        point_max = max(maximum)
        point_min = min(minimum)
        is_signed = True if point_min < 0 else False
        point_max = max(point_max, abs(point_min))
        maxi = 0xffff if not is_signed else 0x7fff
        max_shift = 0
        while point_max < maxi:
            point_max *= 2
            max_shift += 1
        max_shift -= 1
        if max_shift <= 0:
            return 4, 0  # float
        return max_shift, 0x2 + is_signed  # short

    def check(self):
        if self.comp_count > 2:
            AUTO_FIXER.error('Geometry {} comp_count {} out of range'.format(self.name, self.comp_count))
            self.comp_count = 0
        if self.divisor >= 16:
            AUTO_FIXER.error('Geometry {} divisor {} out of range'.format(self.name, self.divisor))
            self.divisor = 0
        if self.format > 5:
            AUTO_FIXER.error('Geometry {} format {} out of range'.format(self.name, self.format))
            self.format = 4

    def __len__(self):
        return self.count

    def unpack(self, binfile):
        binfile.start()
        l = binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, self.comp_count, self.format, self.divisor, self.stride, self.count = binfile.read('3I2BH', 16)

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.comp_count, self.format, self.divisor, self.stride, self.count)


class PointCollection:
    def __init__(self, points, face_indices, minimum=None, maximum=None):
        """
        :param points: multi-dimensional list/array of points
        :param face_indices: ndarray of triangle indices, indexing points
        :param minimum: the minimum value
        :param maximum: the maximum value
        """
        self.points = points
        self.face_indices = face_indices
        self.minimum = minimum if minimum else min(min(x) for x in points)
        self.maximum = maximum if maximum else max(max(x) for x in points)
