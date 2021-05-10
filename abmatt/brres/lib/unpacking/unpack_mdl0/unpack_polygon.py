from abmatt.brres.lib.binfile import UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_bone import unpack_bonetable
from abmatt.brres.mdl0 import polygon as ply
from abmatt.autofix import AutoFix


class UnpackPolygon(Unpacker):
    def __init__(self, name, node, binfile):
        poly = ply.Polygon(name, node, binfile)
        self.encode_string = '>'
        self.indexer = 0
        super(UnpackPolygon, self).__init__(poly, binfile)

    def unpack(self, polygon, binfile):
        binfile.start()
        binfile.readLen()
        mdl0_offset, self.bone_id, cp_vert_lo, cp_vert_hi, xf_vert = binfile.read('2i3I', 20)
        offset = binfile.offset
        vt_dec_size, vt_dec_actual, vt_dec_offset = binfile.read('3I', 12)
        vt_dec_offset += offset
        offset = binfile.offset
        vt_size, vt_actual, vt_offset = binfile.read('3I', 12)
        vt_offset += offset
        self.xf_arry_flags, polygon.flags = binfile.read('2I', 8)
        binfile.advance(4)
        polygon.index, polygon.facepoint_count, polygon.face_count, \
        self.vertex_group_index, self.normal_group_index = binfile.read('3I2h', 16)
        self.color_group_indices = binfile.read('2h', 4)
        self.tex_coord_group_indices = binfile.read('8h', 16)
        if polygon.parent.version >= 10:
            self.fur_vector_id, self.fur_coord_id = binfile.read('2h', 4)
        else:
            self.fur_vector_id = self.fur_coord_id = -1
            # binfile.advance(4)  # ignore
        binfile.store()  # bt offset
        binfile.recall()  # bt
        polygon.bone_table = unpack_bonetable(binfile, 'H')
        binfile.offset = vt_dec_offset + 10
        _, self.cp_vert_lo, _, self.cp_vert_hi = binfile.read('HIHI', 12)
        if self.cp_vert_lo != cp_vert_lo:
            AutoFix.warn('{} CP_VERTEX_LO does not match (using {})'.format(polygon.name, self.cp_vert_lo))
        if self.cp_vert_hi != cp_vert_hi:
            AutoFix.warn('{} CP_VERTEX_HI does not match (using {})'.format(polygon.name, self.cp_vert_hi))
        binfile.advance(5)
        [self.xf_vert] = binfile.read('I', 4)
        if self.xf_vert != xf_vert:
            AutoFix.warn('{} XF_VERT_SPEC does not match (using {})'.format(polygon.name, xf_vert))
        binfile.offset = vt_dec_offset + 32
        uvat = binfile.read('HIHIHI', 18)
        # self.uvat = uvat
        self.parse_uvat(polygon, uvat[1], uvat[3], uvat[5])
        binfile.offset = vt_offset
        polygon.data = binfile.readRemaining()
        # print('\n\n{}\tfacecount:{} data length:{} '.format(self.name, self.face_count, len(self.vt_data)))
        # if self.face_count < 30:
        #     printCollectionHex(self.vt_data)
        binfile.end()

    def post_unpack(self):
        poly = self.node
        mdl0 = poly.parent
        self.parse_xf_arry_flags(self.xf_arry_flags)
        self.parse_xf_vertex_specs(self.xf_vert)
        self.parse_cp_vertex_format(poly, self.cp_vert_hi, self.cp_vert_lo)
        # hook up references
        if self.vertex_group_index >= 0:
            poly.vertices = mdl0.vertices[self.vertex_group_index]
        else:
            poly.vertices = None
        if self.normal_group_index >= 0:
            poly.normals = mdl0.normals[self.normal_group_index]
        else:
            poly.normals = None
        poly.colors = colors = []
        for x in self.color_group_indices:
            if x >= 0:
                colors.append(mdl0.colors[x])
            else:
                colors.append(None)
        poly.uvs = uvs = []
        for x in self.tex_coord_group_indices:
            if x >= 0:
                uvs.append(mdl0.uvs[x])
            else:
                uvs.append(None)
        poly.encode_str = self.encode_string
        if self.bone_id >= 0:
            poly.linked_bone = mdl0.bones[mdl0.bone_table[self.bone_id]]
        else:
            poly.linked_bone = None

    def i_pp(self):
        i = self.indexer
        self.indexer += 1
        return i

    def get_index_decoder(self, index):
        if index == ply.INDEX_FORMAT_NONE:
            return None
        elif index == ply.INDEX_FORMAT_BYTE:
            return 'B'
        elif index == ply.INDEX_FORMAT_SHORT:
            return 'H'
        elif index == 1:
            raise UnpackingError(self.binfile, f'Polygon {self.node.name} has direct indices, which are not supported')
        else:
            raise UnpackingError(self.binfile, f'Polygon {self.node.name} index format {index} out of range')

    def get_index_from_format(self, index):
        decoder = self.get_index_decoder(index)
        if decoder:
            self.encode_string += decoder
            return self.i_pp()
        return -1

    def parse_xf_arry_flags(self, xf_arry_flags):
        self.has_weights = xf_arry_flags & 1
        self.has_uv_matrix = [xf_arry_flags >> i & 1 for i in range(1, 9)]
        xf_arry_flags >>= 9
        self.has_vertex = xf_arry_flags & 1
        self.has_normals = xf_arry_flags & 2
        self.has_color0 = xf_arry_flags & 4
        self.has_color1 = xf_arry_flags & 8
        xf_arry_flags >>= 4
        self.has_uv_group = [xf_arry_flags >> i & 1 for i in range(8)]

    def parse_cp_vertex_format(self, polygon, hi, lo):
        if lo & 0x1:
            polygon.weight_index = self.i_pp()
            self.encode_string += 'B'
        else:
            polygon.weight_index = -1
        self.__check_helper(lo & 0x1, self.has_weights, 'weight')
        lo >>= 1
        tex_matrix = []
        for i in range(8):
            if lo & 1:
                tex_matrix.append(self.i_pp())
                self.encode_string += 'B'
            else:
                tex_matrix.append(-1)
            self.__check_helper(lo & 1, self.has_uv_matrix[i], 'uv_matrix' + str(i))
            lo >>= 1
        polygon.uv_mtx_indices = tex_matrix
        polygon.vertex_index = self.get_index_from_format(lo & 0x3)
        self.__check_helper(polygon.vertex_index >= 0, self.has_vertex, 'vertex')
        polygon.normal_index = self.get_index_from_format(lo >> 2 & 0x3)
        self.__check_helper(polygon.normal_index >= 0, self.has_normals, 'normal')
        polygon.color0_index = self.get_index_from_format(lo >> 4 & 0x3)
        self.__check_helper(polygon.color0_index >= 0, self.has_color0, 'color0')
        polygon.color1_index = self.get_index_from_format(lo >> 6 & 0x3)
        self.__check_helper(polygon.color1_index >= 0, self.has_color1, 'color1')
        polygon.color_count = (polygon.color0_index >= 0) + (polygon.color1_index >= 0)
        self.__check_helper(polygon.color_count, self.color_count, 'color count')
        tex = []
        total = 0
        for i in range(8):
            index = self.get_index_from_format(hi & 3)
            tex.append(index)
            self.__check_helper(index >= 0, self.has_uv_group[i], 'uv' + str(i))
            total += (index >= 0)
            hi >>= 2
        polygon.uv_count = total
        if polygon.uv_count != self.uv_count:
            AutoFix.warn('{} mismatch in {} definition (assuming {})'.format(self.node.name, 'UV count', polygon.uv_count))
        self.__check_helper(polygon.uv_count, self.uv_count, 'uv count')
        polygon.uv_indices = tex

    def __check_helper(self, actual_exists, exists, def_name):
        if bool(actual_exists) != bool(exists):
            has_str = 'has' if actual_exists else 'None'
            AutoFix.warn('{} mismatch in {} definition (assuming {})'.format(self.node.name, def_name, has_str))

    def parse_uvat(self, polygon, uvata, uvatb, uvatc):
        # Since we hook the references to their groups, we don't need the formats etc
        #   This may change if we support direct indexing
        #   Unclear what the e's are so we still parse them
        polygon.vertex_e = uvata & 0x1
        # polygon.vertex_format = uvata >> 1 & 0x7
        # polygon.vertex_divisor = uvata >> 4 & 0x1f
        polygon.normal_e = uvata >> 9 & 1
        # polygon.normal_format = uvata >> 10 & 7
        polygon.color0_e = uvata >> 13 & 1
        # polygon.color0_format = uvata >> 14 & 7
        polygon.color1_e = uvata >> 17 & 1
        # polygon.color1_format = uvata >> 18 & 7

        # polygon.tex_format = [0] * 8
        # polygon.tex_divisor = [0] * 8
        polygon.tex_e[0] = uvata >> 21 & 1
        # polygon.tex_format[0] = uvata >> 22 & 7
        # polygon.tex_divisor[0] = uvata >> 25 & 0x1f
        polygon.normal_index3 = uvata >> 31
        for i in range(1, 4):
            polygon.tex_e[i] = uvatb & 1
            # polygon.tex_format[i] = uvatb >> 1 & 0x7
            # polygon.tex_divisor[i] = uvatb >> 4 & 0x1f
            uvatb >>= 9
        polygon.tex_e[4] = uvatb & 1
        # polygon.tex_format[4] = uvatb >> 1 & 0x7
        # polygon.tex_divisor[4] = uvatc & 0x1f
        uvatc >>= 5
        for i in range(5, 8):
            polygon.tex_e[i] = uvatc & 0x1
            # polygon.tex_format[i] = uvatc >> 1 & 0x7
            # polygon.tex_divisor[i] = uvatc >> 4 & 0x1f
            uvatc >>= 9

    def parse_xf_vertex_specs(self, vt_specs):
        poly = self.node
        self.color_count = vt_specs & 0x3
        normals = vt_specs >> 2 & 0x3
        self.uv_count = vt_specs >> 4 & 0xf

