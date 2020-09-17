"""Objects (Polygons)"""

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.lib.node import Node, get_item_by_index


class Polygon(Node):
    INDEX_FORMAT_NONE = 0
    INDEX_FORMAT_DIRECT = 1
    INDEX_FORMAT_BYTE = 2
    INDEX_FORMAT_SHORT = 3

    def __init__(self, name, parent, binfile=None):
        self.tex_index_format = [0] * 8
        self.tex_format = [0] * 8
        self.tex_divisor = [0] * 8
        self.tex_e = [1] * 8
        super(Polygon, self).__init__(name, parent, binfile)

    @staticmethod
    def get_fmt_str(index_format):
        if index_format == Polygon.INDEX_FORMAT_BYTE:
            return 'B'
        elif index_format == Polygon.INDEX_FORMAT_SHORT:
            return 'H'
        elif index_format == Polygon.INDEX_FORMAT_DIRECT:
            raise NotImplementedError('Index format direct is not supported')
        return ''

    def begin(self):
        self.vertex_index_format = self.INDEX_FORMAT_BYTE
        self.normal_index_format = self.INDEX_FORMAT_BYTE
        self.color0_index_format = self.INDEX_FORMAT_BYTE
        self.color1_index_format = self.INDEX_FORMAT_NONE
        self.vertex_format = 4
        self.has_pos_matrix = False
        self.has_tex_matrix = [False] * 8
        self.vertex_divisor = 0
        self.normal_format = 4
        self.color0_has_alpha = 5
        self.color1_has_alpha = 5
        self.num_colors = 1
        self.normal_type = 0
        self.num_tex = 1
        self.facepoint_count = 0
        self.face_count = 0
        self.flags = 0
        self.index = 0
        self.bone = 0
        self.bone_table = None
        self.vertex_group_index = 0
        self.normal_group_index = 0
        self.color_group_indices = [0, -1]
        self.tex_coord_group_indices = [0] + [-1] * 7
        self.fur_vector_id = -1
        self.fur_coord_id = -1
        self.vertex_e = 1
        self.normal_index3 = self.normal_e = 0
        self.color0_e = self.color1_e = 1

    def get_vertex_group(self):
        if self.vertex_index_format >= self.INDEX_FORMAT_BYTE:
            return self.parent.vertices[self.vertex_group_index]

    def get_normal_group(self):
        if self.normal_index_format >= self.INDEX_FORMAT_BYTE:
            return self.parent.normals[self.normal_group_index]

    def get_tex_group(self, tex_i=0):
        if self.tex_index_format[tex_i] >= self.INDEX_FORMAT_BYTE:
            return self.parent.texCoords[self.tex_coord_group_indices[tex_i]]

    def get_color_group(self, i=0):
        if i == 0:
            if self.color0_index_format >= self.INDEX_FORMAT_BYTE:
                return self.parent.colors[self.color_group_indices[0]]
        elif i == 1:
            if self.color1_index_format >= self.INDEX_FORMAT_BYTE:
                return self.parent.colors[self.color_group_indices[1]]

    def get_material(self):
        definition = self.parent.get_definition_by_object_id(self.index)
        return get_item_by_index(self.parent.materials, definition.matIndex)

    def get_bone(self):
        definition = self.parent.get_definition_by_object_id(self.index)
        return get_item_by_index(self.parent.bones, definition.boneIndex)

    def check(self):
        vertices = self.get_vertex_group()
        if vertices:
            if self.vertex_format != vertices.format:
                AUTO_FIXER.warn('Mismatching format for vertices {}'.format(self.name))
                self.vertex_format = vertices.format
            if self.vertex_divisor != vertices.divisor:
                AUTO_FIXER.warn('Mismatching divisor for vertices {}'.format(self.name))
                self.vertex_divisor = vertices.divisor
        normals = self.get_normal_group()
        if normals:
            if self.normal_format != normals.format:
                AUTO_FIXER.warn('Mismatching format for normals {}'.format(self.name))
                self.normal_format = normals.format
        for i in range(8):
            tex = self.get_tex_group(i)
            if tex:
                if self.tex_format[i] != tex.format:
                    AUTO_FIXER.warn('Mismatching format for uv group {} {} '.format(i, self.name))
                    self.tex_format[i] = tex.format
                if self.tex_divisor[i] != tex.divisor:
                    AUTO_FIXER.warn('Mismatching divisor for uv group {} {}'.format(i, self.name))
                    self.tex_divisor[i] = tex.divisor
            else:
                break

    # --------------------------------------------------
    # PACKING
    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        hi, lo = self.get_cp_vertex_format()
        xf_specs = self.get_xf_vertex_specs()
        binfile.write('i3I', self.bone, lo, hi, xf_specs)
        binfile.write('3I', 0xe0, 0x80, 0)
        vt_dec_offset = binfile.offset - 4
        vt_data_len = len(self.vt_data)
        binfile.write('3I', vt_data_len, vt_data_len, 0)
        vt_offset = binfile.offset - 4
        binfile.write('2I', self.get_xf_array_flags(), self.flags)
        binfile.storeNameRef(self.name)
        binfile.write('3I2h', self.index, self.facepoint_count, self.face_count,
                      self.vertex_group_index, self.normal_group_index)
        binfile.write('2h', *self.color_group_indices)
        binfile.write('8h', *self.tex_coord_group_indices)
        if self.parent.version >= 10:
            binfile.write('2h', self.fur_vector_id, self.fur_coord_id)
        binfile.mark()
        # bone table
        binfile.createRef()
        l = len(self.bone_table) if self.bone_table else 0
        binfile.write('I', l)
        if l:
            binfile.write('{}H'.format(l), *self.bone_table)
        binfile.align()
        # vertex declaration
        dec_ref = binfile.offset - vt_dec_offset + 8
        end_dec = binfile.offset + 0xe0
        binfile.writeOffset('I', vt_dec_offset, dec_ref)
        binfile.advance(10)
        binfile.write('HIHI', 0x0850, lo, 0x0860, hi)
        binfile.write('B2HIB', 0x10, 0, 0x1008, xf_specs, 0)
        uvat = self.get_uvat()
        # if uvat[0] != self.uvat[1] or uvat[1] != self.uvat[3] or uvat[2] != self.uvat[5]:
        #     print('No match!')
        binfile.write('HIHIHI', 0x0870, uvat[0], 0x0880, uvat[1], 0x0890, uvat[2])
        binfile.advance(end_dec - binfile.offset)
        # vertex data
        vt_ref = binfile.offset - vt_offset + 8
        binfile.writeOffset('I', vt_offset, vt_ref)
        binfile.writeRemaining(self.vt_data)
        binfile.alignAndEnd()

    def unpack(self, binfile):
        binfile.start()
        binfile.readLen()
        mdl0_offset, self.bone, cp_vert_lo, cp_vert_hi, xf_vert = binfile.read('2i3I', 20)
        self.parse_cp_vertex_format(cp_vert_hi, cp_vert_lo)
        self.parse_xf_vertex_specs(xf_vert)
        offset = binfile.offset
        vt_dec_size, vt_dec_actual, vt_dec_offset = binfile.read('3I', 12)
        vt_dec_offset += offset
        offset = binfile.offset
        vt_size, vt_actual, vt_offset = binfile.read('3I', 12)
        vt_offset += offset
        xf_arry_flags, self.flags = binfile.read('2I', 8)
        binfile.advance(4)
        self.index, self.facepoint_count, self.face_count, \
        self.vertex_group_index, self.normal_group_index = binfile.read('3I2h', 16)
        self.color_group_indices = binfile.read('2h', 4)
        self.tex_coord_group_indices = binfile.read('8h', 16)
        if self.parent.version >= 10:
            self.fur_vector_id, self.fur_coord_id = binfile.read('2h', 4)
            # binfile.advance(4)  # ignore
        binfile.store()  # bt offset
        binfile.recall()  # bt
        [bt_length] = binfile.read('I', 4)
        self.bone_table = binfile.read('{}H'.format(bt_length), bt_length * 2) if bt_length > 0 else None
        binfile.offset = vt_dec_offset + 32  # ignores most of the beginning since we already have it
        uvat = binfile.read('HIHIHI', 18)
        # self.uvat = uvat
        self.parse_uvat(uvat[1], uvat[3], uvat[5])
        binfile.offset = vt_offset
        self.vt_data = binfile.readRemaining()
        # print('\n\n{}\tfacecount:{} data length:{} '.format(self.name, self.face_count, len(self.vt_data)))
        # if self.face_count < 30:
        #     printCollectionHex(self.vt_data)
        binfile.end()

    def parse_cp_vertex_format(self, hi, lo):
        self.has_pos_matrix = bool(lo & 0x1)
        lo >>= 1
        self.has_tex_matrix = has_tex_matrix = []
        for i in range(8):
            has_tex_matrix.append(bool(lo & 1))
            lo >>= 1
        self.vertex_index_format = lo & 0x3
        self.normal_index_format = lo >> 2 & 0x3
        self.color0_index_format = lo >> 4 & 0x3
        self.color1_index_format = lo >> 6 & 0x3
        for i in range(8):
            self.tex_index_format[i] = hi & 3
            hi >>= 2

    def get_cp_vertex_format(self):
        lo = self.has_pos_matrix
        for i in range(8):
            lo |= self.has_tex_matrix[i] << i + 1
        lo |= (self.vertex_index_format | self.normal_index_format << 2
              | self.color0_index_format << 4 | self.color1_index_format << 6) << 9
        shifter = hi = 0
        for x in self.tex_index_format:
            hi |= x << shifter
            shifter += 2
        return hi, lo

    def parse_uvat(self, uvata, uvatb, uvatc):
        self.vertex_e = uvata & 0x1
        self.vertex_format = uvata >> 1 & 0x7
        self.vertex_divisor = uvata >> 4 & 0x1f
        self.normal_e = uvata >> 9 & 1
        self.normal_format = uvata >> 10 & 7
        self.color0_e = uvata >> 13 & 1
        self.color0_has_alpha = uvata >> 14 & 7
        self.color1_e = uvata >> 17 & 1
        self.color1_has_alpha = uvata >> 18 & 7
        self.tex_e[0] = uvata >> 21 & 1
        self.tex_format[0] = uvata >> 22 & 7
        self.tex_divisor[0] = uvata >> 25 & 0x1f
        self.normal_index3 = uvata >> 31
        for i in range(1, 4):
            self.tex_e[i] = uvatb & 1
            self.tex_format[i] = uvatb >> 1 & 0x7
            self.tex_divisor[i] = uvatb >> 4 & 0x1f
            uvatb >>= 9
        self.tex_e[4] = uvatb & 1
        self.tex_format[4] = uvatb >> 1
        self.tex_divisor[4] = uvatc & 0x1f
        uvatc >>= 5
        for i in range(5, 8):
            self.tex_e[i] = uvatc & 0x1
            self.tex_format[i] = uvatc >> 1 & 0x7
            self.tex_divisor[i] = uvatc >> 4 & 0x1f
            uvatc >>= 9

    def has_vertex_data(self):
        return self.vertex_index_format > 0

    def has_normal_data(self):
        return self.normal_index_format > 0

    def has_color0_data(self):
        return self.color0_index_format > 0

    def has_color1_data(self):
        return self.color1_index_format > 0

    def has_tex_data(self, i):
        return self.tex_index_format[i] > 0

    def get_uvat(self):
        tex_format = self.tex_format
        tex_divisor = self.tex_divisor
        tex_e = self.tex_e
        uvata = self.vertex_e | self.vertex_format << 1 | self.vertex_divisor << 4 \
                | self.normal_e << 9 | self.normal_format << 10 \
                | self.color0_e << 13 | self.color0_has_alpha << 14 \
                | self.color1_e << 17 | self.color1_has_alpha << 18 \
                | tex_e[0] << 21 | tex_format[0] << 22 | tex_divisor[0] << 25 \
                | 1 << 30 | self.normal_index3 << 31

        shifter = uvatb = 0
        for i in range(1, 4):
            uvatb |= (tex_format[i] << 1 | tex_divisor[i] << 4 | tex_e[i]) << shifter
            shifter += 9
        uvatb |= self.tex_e[4] << shifter | tex_format[4] << shifter + 1 | 1 << 31
        shifter = 5
        uvatc = tex_divisor[4]
        for i in range(5, 8):
            uvatc |= (tex_e[i] | tex_format[i] << 1 | tex_divisor[i] << 3) << shifter
            shifter += 9
        return uvata, uvatb, uvatc

    def parse_xf_vertex_specs(self, vt_specs):
        self.num_colors = vt_specs & 0x3
        self.normal_type = vt_specs >> 2 & 0x3
        self.num_tex = vt_specs >> 4 & 0xf

    def get_xf_vertex_specs(self):
        return self.num_colors | self.normal_type << 2 | self.num_tex << 4

    def get_xf_array_flags(self):
        flag = 1 if self.vertex_index_format else 0
        if self.normal_index_format:
            flag |= 0x2
        if self.color0_index_format:
            flag |= 0x4
        if self.color1_index_format:
            flag |= 0x8
        bit = 0x10
        for x in self.tex_index_format:
            if x:
                flag |= bit
            bit <<= 1
        flag <<= 9
        flag |= self.has_pos_matrix
        for i in range(8):
            flag |= self.has_tex_matrix[i] << i + 1
        return flag
