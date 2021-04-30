from abmatt.brres.lib.packing.interface import Packer
from abmatt.brres.lib.packing.pack_mdl0 import xf


class PackPolygon(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    # --------------------------------------------------
    # PACKING
    def pack(self, poly, binfile):
        start = binfile.start()
        # binfile.polygon_offsets.append((start, poly.name))   #- debug
        binfile.markLen()
        binfile.writeOuterOffset()
        hi, lo = self.get_cp_vertex_format()
        xf_specs = self.get_xf_vertex_specs()
        binfile.write('i3I', self.get_bone_id(poly.linked_bone), lo, hi, xf_specs)
        binfile.write('3I', 0xe0, 0x80, 0)
        vt_dec_offset = binfile.offset - 4
        data_len = len(poly.data)
        # binfile.linked_offsets.extend([binfile.offset, binfile.offset + 4])   #- debug
        binfile.write('3I', data_len, data_len, 0)
        vt_offset = binfile.offset - 4
        binfile.write('2I', self.get_xf_array_flags(), poly.flags)
        binfile.storeNameRef(poly.name)
        # binfile.linked_offsets.extend([binfile.offset + 4, binfile.offset + 8])     #- debug
        binfile.write('3I2h', self.index, poly.facepoint_count, poly.face_count,
                      self.get_item_id(poly.get_vertex_group()), self.get_item_id(poly.get_normal_group()))
        # binfile.linked_offsets.append(binfile.offset)   #- debug
        binfile.write('2h', self.get_item_id(poly.get_color_group(0)), self.get_item_id(poly.get_color_group(1)))
        binfile.write('8h', *[self.get_item_id(x) for x in poly.get_uvs()])
        if poly.parent.version >= 10:
            binfile.write('2h', -1, -1)  # Fur vector/coord
        binfile.mark()
        # bone table
        binfile.createRef()
        l = len(poly.bone_table) if poly.bone_table else 0
        binfile.write('I', l)
        if l:
            binfile.write('{}H'.format(l), *poly.bone_table)
        binfile.align()
        # vertex declaration
        dec_ref = binfile.offset - vt_dec_offset + 8
        end_dec = binfile.offset + 0xe0
        binfile.writeOffset('I', vt_dec_offset, dec_ref)
        binfile.advance(10)
        binfile.write('HIHI', 0x0850, lo, 0x0860, hi)
        xf.pack_vt_specs(binfile, xf_specs)
        binfile.advance(1)
        uvat = self.get_uvat()
        # if uvat[0] != self.uvat[1] or uvat[1] != self.uvat[3] or uvat[2] != self.uvat[5]:
        #     print('No match!')
        binfile.write('HIHIHI', 0x0870, uvat[0], 0x0880, uvat[1], 0x0890, uvat[2])
        binfile.advance(end_dec - binfile.offset)
        # vertex data
        vt_ref = binfile.offset - vt_offset + 8
        binfile.writeOffset('I', vt_offset, vt_ref)
        #- debug    Allows us to ignore differences in construction of triangles
        # binfile.linked_offsets.extend([i for i in range(binfile.offset, binfile.offset + len(poly.data))])
        #- end debug
        binfile.writeRemaining(poly.data)
        binfile.end()

    def get_cp_vertex_format(self):
        poly = self.node
        lo = poly.has_weighted_matrix()
        for i in range(8):
            lo |= poly.has_uv_matrix(i) << i + 1

        lo |= (poly.get_index_type(poly.get_vertex_index())
               | poly.get_index_type(poly.get_normal_index()) << 2
               | poly.get_index_type(poly.get_color0_index()) << 4
               | poly.get_index_type(poly.get_color1_index()) << 6) << 9
        shifter = hi = 0
        for uv_i in poly.uv_indices:
            x = poly.get_index_type(uv_i)
            hi |= x << shifter
            shifter += 2
        return hi, lo

    def get_bone_id(self, bone):
        if bone:
            return bone.index
        return 0

    def get_item_id(self, point):
        if point:
            return point.index
        return -1

    def get_format(self, point):
        if point:
            return point.get_format()
        return 0

    def get_format_color(self, color):
        if color:
            return color.get_format()
        return 5

    def get_format_uv(self, uv):
        if uv:
            return uv.get_format()
        return 4

    def get_divisor(self, point):
        if point:
            return point.get_divisor()
        return 0

    def get_uvat(self):
        poly = self.node
        vert = poly.get_vertex_group()
        normal = poly.get_normal_group()
        color0 = poly.get_color_group(0)
        color1 = poly.get_color_group(1)
        uvs = poly.get_uvs()
        tex_e = poly.tex_e
        uvata = poly.vertex_e | self.get_format(vert) << 1 | self.get_divisor(vert) << 4 \
                | poly.normal_e << 9 | self.get_format_uv(normal) << 10 \
                | poly.color0_e << 13 | self.get_format_color(color0) << 14 \
                | poly.color1_e << 17 | self.get_format_color(color1) << 18 \
                | tex_e[0] << 21 | self.get_format_uv(uvs[0]) << 22 | self.get_divisor(uvs[0]) << 25 \
                | 1 << 30 | poly.normal_index3 << 31

        shifter = uvatb = 0
        for i in range(1, 4):
            uvatb |= (self.get_format_uv(uvs[i]) << 1 | self.get_divisor(uvs[i]) << 4 | tex_e[i]) << shifter
            shifter += 9
        uvatb |= poly.tex_e[4] << shifter | self.get_format_uv(uvs[4]) << shifter + 1 | 1 << 31
        shifter = 5
        uvatc = self.get_divisor(uvs[4])
        for i in range(5, 8):
            uvatc |= (tex_e[i] | self.get_format_uv(uvs[i]) << 1 | self.get_divisor(uvs[i]) << 3) << shifter
            shifter += 9
        return uvata, uvatb, uvatc

    def get_xf_vertex_specs(self):
        poly = self.node
        return poly.count_colors() | poly.has_normals() << 2 | poly.count_uvs() << 4

    def get_xf_array_flags(self):
        poly = self.node
        flag = 1 if poly.has_vertices() else 0
        if poly.has_normals():
            flag |= 0x2
        if poly.has_color0():
            flag |= 0x4
        if poly.has_color1():
            flag |= 0x8
        bit = 0x10
        for i in range(8):
            if poly.has_uv_group(i):
                flag |= bit
            bit <<= 1
        flag <<= 9
        flag |= poly.has_weighted_matrix()
        for i in range(8):
            flag |= poly.has_uv_matrix(i) << i + 1
        return flag
