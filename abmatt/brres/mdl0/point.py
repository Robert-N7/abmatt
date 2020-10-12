from autofix import AutoFix
from abmatt.brres.lib.node import Node


class Point(Node):
    FMT = ('B', 'b', 'H', 'h', 'f')

    def __str__(self):
        return self.name + ' component_count:' + str(self.comp_count) + ' divisor:' + str(self.divisor) + \
               ' format:' + str(self.format) + ' stride:' + str(self.stride) + ' count:' + str(self.count)

    def begin(self):
        self.data = []

    def check(self):
        result = False
        if self.comp_count > 2:
            AutoFix.get().error('Geometry {} comp_count {} out of range'.format(self.name, self.comp_count))
            self.comp_count = 0
            result = True
        if self.divisor >= 16:
            AutoFix.get().error('Geometry {} divisor {} out of range'.format(self.name, self.divisor))
            self.divisor = 0
            result = True
        if self.format > 5:
            AutoFix.get().error('Geometry {} format {} out of range'.format(self.name, self.format))
            self.format = 4
            result = True
        return result

    def __len__(self):
        return self.count

    def unpack_data(self, binfile):
        binfile.recall()
        fmt = '{}{}'.format(self.COMP_COUNT[self.comp_count], self.FMT[self.format])
        stride = self.stride
        data = []
        for i in range(self.count):
            data.append(binfile.read(fmt, stride))
        binfile.alignAndEnd()
        self.data = data
        return data

    def pack_data(self, binfile):
        binfile.align()
        binfile.createRef()
        fmt = '{}{}'.format(self.COMP_COUNT[self.comp_count], self.FMT[self.format])
        data = self.data
        for x in data:
            binfile.write(fmt, *x)
        binfile.alignAndEnd()

    def unpack(self, binfile):
        binfile.start()
        l = binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, self.comp_count, self.format, self.divisor, self.stride, self.count = binfile.read('3I2BH', 16)
        # print(self)

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.comp_count, self.format, self.divisor, self.stride, self.count)
