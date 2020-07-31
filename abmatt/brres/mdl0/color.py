from brres.lib.node import Node


class Color(Node):
    def unpack(self, binfile):
        binfile.start()
        binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, self.has_alpha, self.format, self.stride, self.flags, self.count = binfile.read('3I2BH', 16)
        binfile.recall()
        self.data = binfile.readRemaining()
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
        binfile.end()
