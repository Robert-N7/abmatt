from abmatt.autofix import AutoFix
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.mdl0 import point
from abmatt.brres.mdl0.normal import Normal
from abmatt.brres.mdl0.texcoord import TexCoord
from abmatt.brres.mdl0.vertex import Vertex


def is_valid_format(format):
    return 0 <= format < 5


class UnpackPoint(Unpacker):
    def is_valid_comp_count(self, comp_count):
        return 0 <= comp_count < 2

    def unpack(self, pt, binfile):
        start = binfile.start()
        l = binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        pt.index, pt.comp_count, pt.format, pt.divisor, pt.stride, pt.count = binfile.read('3I2BH', 16)
        if not self.is_valid_comp_count(pt.comp_count):
            AutoFix.error('{} has invalid component count {}, using default {}'.format(pt.name, pt.comp_count,
                                                                                             pt.default_comp_count))
            pt.comp_count = pt.default_comp_count
        if not is_valid_format(pt.format):
            # determine the format using the file length
            binfile.recall(pop=False)
            old_format = pt.format
            bytes_remaining = start + l - binfile.offset
            width = bytes_remaining // (pt.count * pt.comp_count)
            if width >= 4:
                pt.format = point.FMT_FLOAT
            elif width >= 2:        # assumes unsigned
                pt.format = point.FMT_INT16
            else:
                pt.format = point.FMT_INT8
            AutoFix.error('{} has invalid format {}, using format {}'.format(pt.name, old_format,
                                                                                   point.FMT_STR[pt.format]))
        # print(self)

    def unpack_data(self, point, binfile):
        binfile.recall()
        fmt = '{}{}'.format(point.point_width, point.format_str)
        stride = point.stride
        data = []
        for i in range(point.count):
            data.append(binfile.read(fmt, stride))
        binfile.alignAndEnd()
        point.data = data


class UnpackVertex(UnpackPoint):

    def __init__(self, name, node, binfile):
        v = Vertex(name, node, binfile)
        super().__init__(v, binfile)

    def unpack(self, vertex, binfile):
        super(UnpackVertex, self).unpack(vertex, binfile)
        vertex.minimum = binfile.read('3f', 12)
        vertex.maximum = binfile.read('3f', 12)
        self.unpack_data(vertex, binfile)


class UnpackNormal(UnpackPoint):
    def is_valid_comp_count(self, comp_count):
        return 0 <= comp_count < 3

    def __init__(self, name, node, binfile):
        n = Normal(name, node, binfile)
        super().__init__(n, binfile)

    def unpack(self, normal, binfile):
        super(UnpackNormal, self).unpack(normal, binfile)
        if normal.comp_count == 32:     # special case (not really sure the differences in types)
            normal.normal_type = 2
            normal.comp_count = 3
        else:
            normal.normal_type = 1 if normal.comp_count == 9 else 0
        self.unpack_data(normal, binfile)


class UnpackUV(UnpackPoint):
    def __init__(self, name, node, binfile):
        uv = TexCoord(name, node, binfile)
        super().__init__(uv, binfile)

    def unpack(self, uv, binfile):
        super(UnpackUV, self).unpack(uv, binfile)
        uv.minimum = binfile.read('2f', 8)
        uv.maximum = binfile.read('2f', 8)
        self.unpack_data(uv, binfile)
