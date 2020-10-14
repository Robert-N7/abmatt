from abmatt.brres.lib.node import Node


class Color(Node):

    def begin(self):
        self.flags = 0
        self.index = 0
        self.count = 0

    def __len__(self):
        return self.count

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.has_alpha, self.format, self.stride, self.flags, self.count)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()


