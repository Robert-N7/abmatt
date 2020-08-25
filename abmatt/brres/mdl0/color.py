from struct import pack

from brres.lib.node import Node


class Color(Node):

    def begin(self):
        self.flags = 0
        self.index = 0

    def __len__(self):
        return self.count

    def unpack(self, binfile):
        binfile.start()
        binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, self.has_alpha, self.format, self.stride, self.flags, self.count = binfile.read('3I2BH', 16)
        binfile.recall()
        self.data = binfile.readRemaining()
        print('Color {} count {}'.format(self.name, self.count))
        binfile.end()

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.has_alpha, self.format, self.stride, self.flags, self.count)
        binfile.align()
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()


