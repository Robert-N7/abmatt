from autofix import AutoFix
from abmatt.brres.lib.node import Node


class Point(Node):
    @property
    def DEFAULT_WIDTH(self):
        return 3

    def __str__(self):
        return self.name + ' component_count:' + str(self.comp_count) + ' divisor:' + str(self.divisor) + \
               ' format:' + str(self.format) + ' stride:' + str(self.stride) + ' count:' + str(self.count)

    def begin(self):
        self.data = []
        self.comp_count = self.DEFAULT_WIDTH
        self.format = 4
        self.divisor = 0
        self.stride = 0


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

    def pack_data(self, binfile):
        binfile.align()
        binfile.createRef()
        fmt = '{}{}'.format(self.COMP_COUNT[self.comp_count], self.FMT[self.format])
        data = self.data
        for x in data:
            binfile.write(fmt, *x)
        binfile.alignAndEnd()


    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.comp_count, self.format, self.divisor, self.stride, self.count)
