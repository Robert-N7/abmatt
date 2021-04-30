from abmatt.brres.lib.packing.interface import Packer


class PackColor(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack(self, color, binfile):
        binfile.start()
        binfile.markLen()
        binfile.writeOuterOffset()
        binfile.mark()
        binfile.storeNameRef(color.name)
        binfile.write('3I2BH', self.index, color.has_alpha, color.format, color.stride, color.flags, color.count)
        binfile.align()
        binfile.createRef()
        # offset = binfile.offset  #- debug
        binfile.writeRemaining(color.data)
        # binfile.linked_offsets.extend(i for i in range(offset, binfile.offset))     #- debug
        binfile.alignAndEnd()
