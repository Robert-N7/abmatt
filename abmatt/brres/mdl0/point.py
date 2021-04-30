from abmatt.autofix import AutoFix
from abmatt.brres.lib.decoder import decode_geometry_group
from abmatt.brres.lib.node import Node

FMT_UINT8 = 0
FMT_INT8 = 1
FMT_UINT16 = 2
FMT_INT16 = 3
FMT_FLOAT = 4
FMT_STR = 'BbHhf'


class Point(Node):
    def __init__(self, name, parent, binfile=None):
        self.decoded = None
        super().__init__(name, parent, binfile)

    @property
    def default_comp_count(self):
        raise NotImplementedError()

    @staticmethod
    def comp_count_from_width(width):
        """Gets comp count corresponding to width"""
        raise NotImplementedError()

    @property
    def point_width(self):
        raise NotImplementedError()

    @property
    def format_str(self):
        return FMT_STR[self.format]

    def __str__(self):
        return self.name + ' component_count:' + str(self.comp_count) + ' divisor:' + str(self.divisor) + \
               ' format:' + str(self.format) + ' stride:' + str(self.stride) + ' count:' + str(self.count)

    def begin(self):
        self.data = []
        self.comp_count = self.default_comp_count
        self.format = 4
        self.divisor = 0
        self.stride = 0
        self.count = 0

    def get_decoded(self):
        if self.decoded is None:
            self.decoded = decode_geometry_group(self)
        return self.decoded

    def __iter__(self):
        return iter(self.get_decoded())

    def __next__(self):
        return next(self.decoded)

    def get_format(self):
        return self.format

    def get_divisor(self):
        return self.divisor

    def get_stride(self):
        return self.stride

    def get_comp_count(self):
        return self.comp_count

    def check(self):
        result = False
        # if self.comp_count > 3 and self.comp_count != 9:
        #     AutoFix.get().error('Geometry {} comp_count {} out of range'.format(self.name, self.comp_count))
        #     self.comp_count = 0
        #     result = True
        if self.divisor >= 16:
            AutoFix.get().error('Geometry {} divisor {} out of range'.format(self.name, self.divisor))
            self.divisor = 0
            result = True
        # if self.format > 5:
        #     AutoFix.get().error('Geometry {} format {} out of range'.format(self.name, self.format))
        #     self.format = 4
        #     result = True
        return result

    def __len__(self):
        return self.count
