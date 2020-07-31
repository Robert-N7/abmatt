from brres.lib.autofix import AUTO_FIXER
from brres.lib.node import Node
from brres.lib import binfile


class Geometry(Node):

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

    def unpack(self, binfile):
        binfile.start()
        l = binfile.readLen()
        binfile.advance(4)
        binfile.mark()
        binfile.advance(4)
        self.index, self.comp_count, self.format, self.divisor, self.stride, self.count = binfile.read('3I2BH', 16)

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.comp_count, self.format, self.divisor, self.stride, self.count)
