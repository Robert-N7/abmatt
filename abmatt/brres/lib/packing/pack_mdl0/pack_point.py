from abmatt.brres.lib.packing.interface import Packer


class PackPoint(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack_data(self, binfile):
        point = self.node
        binfile.align()
        binfile.createRef()
        fmt = '{}{}'.format(point.point_width, point.format_str)
        data = point.data
        offset = binfile.offset     #- debug
        for x in data:
            binfile.write(fmt, *x)
        binfile.linked_offsets.extend([i for i in range(offset, binfile.offset)])   #- debug
        binfile.alignAndEnd()

    def pack(self, point, binfile):
        binfile.start()
        binfile.markLen()
        binfile.writeOuterOffset()
        binfile.mark()
        binfile.storeNameRef(point.name)
        binfile.write('3I2BH', self.index, point.comp_count, point.format, point.divisor, point.stride, point.count)


class PackVertex(PackPoint):
    def pack(self, node, binfile):
        """ Packs into binfile """
        super(PackVertex, self).pack(node, binfile)
        binfile.linked_offsets.extend([i for i in range(binfile.offset, binfile.offset + 24, 4)]) #- debug
        binfile.write('3f', *self.node.minimum)
        binfile.write('3f', *self.node.maximum)
        self.pack_data(binfile)


class PackNormal(PackPoint):
    def pack(self, node, binfile):
        super(PackNormal, self).pack(node, binfile)
        self.pack_data(binfile)


class PackUV(PackPoint):
    def pack(self, node, binfile):
        super().pack(node, binfile)
        binfile.linked_offsets.extend([i for i in range(binfile.offset, binfile.offset + 16, 4)])   #- debug
        binfile.write('2f', *self.node.minimum)
        binfile.write('2f', *self.node.maximum)
        self.pack_data(binfile)