from abmatt.brres.lib.packing.interface import Packer


class PackColor(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack(self, color, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(color.name)
        binfile.write('3I2BH', self.index, color.has_alpha, color.format, color.stride, color.flags, color.count)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(color.data)
        binfile.alignAndEnd()
