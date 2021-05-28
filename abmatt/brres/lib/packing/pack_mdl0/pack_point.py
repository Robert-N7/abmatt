from abmatt.lib.pack_interface import Packer


class PackPoint(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack_data(self, binfile):
        point = self.node
        binfile.align()
        binfile.create_ref()
        fmt = '{}{}'.format(point.point_width, point.format_str)
        data = point.data
        # offset = binfile.offset     #- debug
        for x in data:
            binfile.write(fmt, *x)
        # binfile.linked_offsets.extend([i for i in range(offset, binfile.offset)])   #- debug
        binfile.align_and_end()

    def pack(self, point, binfile):
        binfile.start()
        binfile.mark_len()
        binfile.write_outer_offset()
        binfile.mark()
        binfile.store_name_ref(point.name)
        binfile.write('3I2BH', self.index, point.comp_count, point.format, point.divisor, point.stride, point.count)


class PackVertex(PackPoint):
    def pack(self, node, binfile):
        """ Packs into binfile """
        super(PackVertex, self).pack(node, binfile)
        # binfile.linked_offsets.extend([i for i in range(binfile.offset, binfile.offset + 24, 4)]) #- debug
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
        # binfile.linked_offsets.extend([i for i in range(binfile.offset, binfile.offset + 16, 4)])   #- debug
        binfile.write('2f', *self.node.minimum)
        binfile.write('2f', *self.node.maximum)
        self.pack_data(binfile)