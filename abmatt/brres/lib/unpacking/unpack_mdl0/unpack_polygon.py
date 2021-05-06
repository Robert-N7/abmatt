from abmatt.brres.lib.binfile import UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_bone import unpack_bonetable
from abmatt.brres.mdl0 import polygon as ply


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
        self.parse_cp_vertex_format(polygon, cp_vert_hi, cp_vert_lo)
        self.parse_xf_vertex_specs(xf_vert)
        offset = binfile.offset
        vt_dec_size, vt_dec_actual, vt_dec_offset = binfile.read('3I', 12)
        vt_dec_offset += offset
        offset = binfile.offset
        vt_size, vt_actual, vt_offset = binfile.read('3I', 12)
        vt_offset += offset
        xf_arry_flags, polygon.flags = binfile.read('2I', 8)
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
        binfile.offset = vt_dec_offset + 32  # ignores most of the beginning since we already have it
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

    def parse_cp_vertex_format(self, polygon, hi, lo):
        if lo & 0x1:
            polygon.weight_index = self.i_pp()
            self.encode_string += 'B'
        else:
            polygon.weight_index = -1
        lo >>= 1
        tex_matrix = []
        for i in range(8):
            if lo & 1:
                tex_matrix.append(self.i_pp())
                self.encode_string += 'B'
            else:
                tex_matrix.append(-1)
            lo >>= 1
        polygon.uv_mtx_indices = tex_matrix
        polygon.vertex_index = self.get_index_from_format(lo & 0x3)
        polygon.normal_index = self.get_index_from_format(lo >> 2 & 0x3)
        polygon.color0_index = self.get_index_from_format(lo >> 4 & 0x3)
        polygon.color1_index = self.get_index_from_format(lo >> 6 & 0x3)
        tex = []
        for i in range(8):
            tex.append(self.get_index_from_format(hi & 3))
            hi >>= 2
        polygon.uv_indices = tex

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
        poly.color_count = vt_specs & 0x3
        normals = vt_specs >> 2 & 0x3
        poly.uv_count = vt_specs >> 4 & 0xf

