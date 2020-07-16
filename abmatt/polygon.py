"""Objects (Polygons)"""

class Polygon:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    # --------------------------------------------------
    # PACKING
    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.write('12I', *self.head_data0)
        binfile.storeNameRef(self.name)
        binfile.write('3I2H', self.index, self.vertex_count, self.face_count,
                      self.vertex_group_index, self.normal_group_index)
        binfile.write('2H', *self.color_group_indices)
        binfile.write('8H', *self.tex_coord_group_indices)
        binfile.writeRemaining(self.data)
        binfile.end()

    def unpack(self, binfile):
        binfile.start()
        length, mdl0_offset = binfile.read('Ii', 8)
        self.head_data0 = binfile.read('12I', 48)
        assert self.name == binfile.unpack_name()
        # binfile.advance(4)
        self.index, self.vertex_count, self.face_count, \
        self.vertex_group_index, self.normal_group_index = binfile.read('3I2H', 16)
        self.color_group_indices = binfile.read('2H', 4)
        self.tex_coord_group_indices = binfile.read('8H', 16)
        self.data = binfile.readRemaining(length)
        binfile.end()