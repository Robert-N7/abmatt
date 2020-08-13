"""Objects (Polygons)"""
from struct import pack

from brres.lib.binfile import printCollectionHex
from brres.lib.node import Node


class Polygon(Node):
    INDEX_FORMAT_NONE = 0
    INDEX_FORMAT_DIRECT = 1
    INDEX_FORMAT_BYTE = 2
    INDEX_FORMAT_SHORT = 3

    def __init__(self, name, parent, binfile=None):
        self.tex_index_format = [0] * 8
        self.tex_format = [0] * 8
        self.tex_divisor = [0] * 8
        super(Polygon, self).__init__(name, parent, binfile)

    def begin(self):
        self.vertex_index_format = self.INDEX_FORMAT_BYTE
        self.normal_index_format = self.INDEX_FORMAT_BYTE
        self.color0_index_format = self.INDEX_FORMAT_BYTE
        self.color1_index_format = self.INDEX_FORMAT_NONE
        self.vertex_format = 0
        self.vertex_divisor = 0
        self.normal_format = 0
        self.color0_has_alpha = 0
        self.color1_has_alpha = 0
        self.num_colors = 1
        self.normal_type = 0
        self.num_tex = 1
        self.vertex_count = 0
        self.face_count = 0
        self.flags = 0
        self.index = 0
        self.bone = 0
        self.bone_table = None
        self.vertex_group_index = 0
        self.normal_group_index = 0
        self.color_group_indices = [0, -1] * 2
        self.tex_coord_group_indices = [0] + [-1] * 7

    def encode_data(self, vertex, normal, color, uvs, face_indices):
        # set up vertex declaration
        self.vertex_format = vertex.format
        self.vertex_divisor = vertex.divisor
        if len(vertex) > 0xff:
            self.vertex_index_format = self.INDEX_FORMAT_SHORT
            fmt_str = 'H'
        else:
            fmt_str = 'B'
        self.vertex_count = len(vertex)
        self.vertex_group_index = vertex.index
        if normal:
            self.normal_type = normal.comp_count
            self.normal_group_index = normal.index
            self.normal_format = normal.format
            if len(normal) > 0xff:
                self.normal_index_format = self.INDEX_FORMAT_SHORT
                fmt_str += 'H'
            else:
                fmt_str += 'B'
        else:
            self.normal_index_format = self.INDEX_FORMAT_NONE
        if color:
            if len(color) > 0xff:
                self.color0_index_format = self.INDEX_FORMAT_SHORT
                fmt_str += 'H'
            else:
                fmt_str += 'B'
            self.color0_has_alpha = color.has_alpha
            self.color_group_indices[0] = color.index
        else:
            self.color0_index_format = self.INDEX_FORMAT_NONE
            self.num_colors = 0
        self.num_tex = len(uvs)
        for i in range(len(uvs)):
            uv = uvs[i]
            self.tex_coord_group_indices[i] = uv.index
            self.tex_format[i] = uv.format
            self.tex_divisor[i] = uv.divisor
            if len(uv) > 0xff:
                self.tex_index_format[i] = self.INDEX_FORMAT_SHORT
                fmt_str += 'H'
            else:
                self.tex_index_format[i] = self.INDEX_FORMAT_BYTE
                fmt_str += 'B'
        face_point_len = len(face_indices[0])
        self.face_count = face_point_len / 3
        data = bytearray(pack('>BH', 0x90, face_point_len))
        for i in range(face_point_len):
            data.extend(pack(fmt_str, [x[i] for x in face_indices]))
        self.vt_data = data




    def get_vertex_group(self):
        if self.vertex_index_format >= self.INDEX_FORMAT_BYTE:
            return self.parent.vertices[self.vertex_group_index]

    def get_normal_group(self):
        if self.normal_index_format >= self.INDEX_FORMAT_BYTE:
            return self.parent.normals[self.normal_group_index]

    def get_tex_group(self, tex_i=0):
        if self.tex_index_format[tex_i] >= self.INDEX_FORMAT_BYTE:
            return self.parent.texCoords[self.tex_coord_group_indices[tex_i]]

    def get_color_group(self):
        pass

    def check(self):
        pass

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
        binfile.write('3I2h', self.index, self.vertex_count, self.face_count,
                      self.vertex_group_index, self.normal_group_index)
        binfile.write('2h', *self.color_group_indices)
        binfile.write('8h', *self.tex_coord_group_indices)
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
        binfile.write('HIHIHI', 0x0870, uvat[0], 0x0880, uvat[1], 0x0890, uvat[2])
        binfile.advance(end_dec - binfile.offset)
        # vertex data
        vt_ref = binfile.offset - vt_offset + 8
        binfile.writeOffset('I', vt_offset, vt_ref)
        binfile.write('{}B'.format(len(self.vt_data)), *self.vt_data)
        binfile.alignAndEnd()

    def unpack(self, binfile):
        binfile.start()
        length, mdl0_offset, self.bone, cp_vert_lo, cp_vert_hi, xf_vert = binfile.read('I2i3I', 24)
        self.parse_cp_vertex_format(cp_vert_hi, cp_vert_lo)
        self.parse_xf_vertex_specs(xf_vert)
        offset = binfile.offset
        vt_dec_size, vt_dec_actual, vt_dec_offset = binfile.read('3I', 12)
        vt_dec_offset += offset
        offset = binfile.offset
        vt_size, vt_actual, vt_offset = binfile.read('3I', 12)
        vt_offset += offset
        xf_arry_flags, self.flags = binfile.read('2I', 8)
        assert self.name == binfile.unpack_name()
        self.index, self.vertex_count, self.face_count, \
        self.vertex_group_index, self.normal_group_index = binfile.read('3I2h', 16)
        self.color_group_indices = binfile.read('2h', 4)
        self.tex_coord_group_indices = binfile.read('8h', 16)
        if self.parent.version >= 10:
            binfile.advance(4)  # ignore
        binfile.store()  # bt offset
        binfile.recall()  # bt
        [bt_length] = binfile.read('I', 4)
        self.bone_table = binfile.read('{}H'.format(bt_length), bt_length * 2) if bt_length > 0 else None
        binfile.offset = vt_dec_offset + 12
        assert cp_vert_lo == binfile.read('I', 4)[0]
        binfile.advance(2)
        assert cp_vert_hi == binfile.read('I', 4)[0]
        binfile.advance(5)
        assert xf_vert == binfile.read('I', 5)[0]
        uvat = binfile.read('HIHIHI', 18)
        self.parse_uvat(uvat[1], uvat[3], uvat[5])
        binfile.offset = vt_offset
        self.vt_data = binfile.read('{}B'.format(vt_size), vt_size)
        # print('\n\n' + self.name)
        # printCollectionHex(self.vt_data)
        binfile.end()

    def parse_cp_vertex_format(self, hi, lo):
        lo >>= 9
        self.vertex_index_format = lo & 0x3
        self.normal_index_format = lo >> 2 & 0x3
        self.color0_index_format = lo >> 4 & 0x3
        self.color1_index_format = lo >> 6 & 0x3
        for i in range(8):
            self.tex_index_format[i] = hi & 3
            hi >>= 2

    def get_cp_vertex_format(self):
        lo = (self.vertex_index_format | self.normal_index_format << 2
              | self.color0_index_format << 4 | self.color1_index_format << 6) << 9
        shifter = hi = 0
        for x in self.tex_index_format:
            hi |= x << shifter
            shifter += 2
        return hi, lo

    def parse_uvat(self, uvata, uvatb, uvatc):
        self.vertex_format = uvata >> 1 & 0x7
        self.vertex_divisor = uvata >> 4 & 0x1f
        self.normal_format = uvata >> 10 & 7
        self.color0_has_alpha = uvata >> 14 & 7
        self.color1_has_alpha = uvata >> 18 & 7
        self.tex_format[0] = uvata >> 22 & 7
        self.tex_divisor[0] = uvata >> 25 & 0x1f
        uvatb >>= 1
        for i in range(1, 4):
            self.tex_format[i] = uvatb & 0x7
            self.tex_divisor[i] = uvatb >> 3 & 0x1f
            uvatb >>= 9
        self.tex_format[4] = uvatb
        self.tex_divisor[4] = uvatc & 0x1f
        uvatc >>= 6
        for i in range(5, 8):
            self.tex_format[i] = uvatc & 0x7
            self.tex_divisor[i] = uvatc >> 3 & 0x1f
            uvatc >>= 9

    def get_uvat(self):
        tex_format = self.tex_format
        tex_divisor = self.tex_divisor
        uvata = 0x40222201 | self.vertex_format << 1 | self.vertex_divisor << 4 | self.normal_format << 10 \
                | self.color0_has_alpha << 14 | self.color1_has_alpha << 18 \
                | tex_format[0] << 22 | tex_divisor[0] << 27

        shifter = uvatb = 1
        for i in range(1, 4):
            uvatb |= (tex_format[i] | tex_divisor[i] << 3 | 0x100) << shifter
            shifter += 9
        uvatb |= tex_format[4] << shifter
        shifter = 5
        uvatc = tex_divisor[4]
        for i in range(5, 8):
            uvatc |= (1 | tex_format[i] << 1 | tex_divisor[i] << 3) << shifter
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
        return flag << 9
