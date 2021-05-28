from abmatt.lib.pack_interface import Packer


class PackColor(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def pack(self, color, binfile):
        binfile.start()
        binfile.mark_len()
        binfile.write_outer_offset()
        binfile.mark()
        binfile.store_name_ref(color.name)
        binfile.write('3I2BH', self.index, color.has_alpha, color.format, color.stride, color.flags, color.count)
        binfile.align()
        binfile.create_ref()
        # offset = binfile.offset  #- debug
        binfile.write_remaining(color.data)
        # binfile.linked_offsets.extend(i for i in range(offset, binfile.offset, 4))     #- debug
        binfile.align_and_end()
