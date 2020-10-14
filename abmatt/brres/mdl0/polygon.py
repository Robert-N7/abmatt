"""Objects (Polygons)"""

from autofix import AutoFix, Bug
from abmatt.brres.lib.node import Node, get_item_by_index, Clipable


class Polygon(Clipable):
    @property
    def SETTINGS(self):
        raise NotImplementedError()

    def set_str(self, key, value):
        raise NotImplementedError()

    def get_str(self, key):
        raise NotImplementedError()

    def paste(self, item):
        raise NotImplementedError()

    INDEX_FORMAT_NONE = 0
    INDEX_FORMAT_DIRECT = 1
    INDEX_FORMAT_BYTE = 2
    INDEX_FORMAT_SHORT = 3

    def __init__(self, name, parent, binfile=None):
        # todo, refactor formats to be letters
        self.tex_divisor = [0] * 8
        self.tex_e = [1] * 8
        self.material = None
        self.priority = 0
        self.tri_groups = None
        self.visible_bone = None
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
        self.vertex_index = -1
        self.normal_index = -1
        self.color0_index = -1
        self.color1_index = -1
        self.tex_indices = [-1] * 8
        self.weight_index = -1
        self.tex_mtx_indices = [-1] * 8
        self.vertices = None
        self.facepoint_count = 0
        self.face_count = 0
        self.colors = [None, None]
        self.normals = None
        self.encode_str = ''
        self.uvs = [None] * 8
        self.data = bytearray()
        self.flags = 0
        self.bone = None
        self.visible_bone = self.parent.bones[0]
        self.bone_table = None
        self.fur_vector = None
        self.fur_coord = None
        self.vertex_e = 1
        self.normal_index3 = self.normal_e = 0
        self.color0_e = self.color1_e = 1

    def add_bone_table(self, table):
        self.bone_table = table
        self.bone = -1

    def get_vertex_group(self):
        return self.vertices

    def get_normal_group(self):
        return self.normals

    def has_normals(self):
        return self.normals is not None

    def get_tex_group(self, tex_i=0):
        return self.uvs[tex_i]

    def get_color_group(self, i=0):
        return self.colors[i]

    def set_draw_priority(self, priority):
        if self.priority != priority:
            self.priority = priority
            self.mark_modified()
            return True
        return False

    def get_draw_priority(self):
        return self.priority

    def get_material(self):
        return self.material

    def set_material(self, material):
        my_material = self.get_material()
        if material != my_material:
            self.material = self.parent.update_polygon_material(self, my_material, material)

    def get_bone(self):
        return self.visible_bone

    def check(self, verts, norms, uvs, colors):  # as we go along, gather verts norms uvs colors
        modified = False
        vertices = self.get_vertex_group()
        if vertices:
            verts.add(vertices)
        normals = self.get_normal_group()
        if normals:
            norms.add(normals)
        material = self.get_material()

        # Colors
        my_colors = self.get_color_group()
        uses_vertex_colors = material.is_vertex_color_enabled()
        if my_colors:
            colors.add(my_colors)
            if not uses_vertex_colors:
                AutoFix.get().info(f'{self.name} has unused vertex colors', 4)
        elif uses_vertex_colors:
            b = Bug(2, 2, f'{material.name} uses vertex colors but {self.name} has no colors!',
                    'Disable vertex colors')
            material.enable_vertex_color(False)
            b.resolve()
            modified = True

        # UVs
        uvs_used = material.get_uv_channels()
        uv_count = 0
        for i in range(8):
            tex = self.get_tex_group(i)
            if tex:
                uv_count += 1
                uvs.add(tex)
                if i in uvs_used:
                    uvs_used.remove(i)
                else:
                    AutoFix.get().info(f'{self.name} UV Channel {i} is not used by material.', 3)
            else:
                break
        if uvs_used:
            AutoFix.get().warn(f'{self.name} does not have UV channel(s) {uvs_used} but the material uses them!')
        return modified

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


    def get_bone_table(self):
        return self.bone_table

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
                | self.color0_e << 13 | self.color0_format << 14 \
                | self.color1_e << 17 | self.color1_format << 18 \
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
