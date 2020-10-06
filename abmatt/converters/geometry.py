from struct import unpack_from, pack

import numpy as np

from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex
from converters.colors import ColorCollection
from converters.convert_lib import Converter
from converters.influence import InfluenceCollection
from converters.matrix import get_rotation_matrix, apply_matrix
from converters.points import PointCollection
from converters.triangle import TriangleSet


class Geometry:
    def __init__(self, name, material_name, vertices, texcoords=None, normals=None, colors=None, triangles=None,
                 influences=None, linked_bone=None):
        self.name = name
        self.vertices = vertices
        if texcoords is None:
            self.texcoords = []
        else:
            self.texcoords = texcoords
        self.normals = normals
        self.colors = colors
        self.material_name = material_name
        self.influences = influences
        self.triangles = triangles
        self.linked_bone = linked_bone

    def combine(self, geometry):
        if not self.__geometry_matches(geometry):
            return False
        self.vertices.combine(geometry.vertices)
        mine = self.texcoords
        theres = geometry.texcoords
        for i in range(len(mine)):
            mine[i].combine(theres[i])
        if self.normals:
            self.normals.combine(geometry.normals)
        if self.colors:
            self.colors.combine(geometry.colors)
        if self.influences:
            self.influences.combine(geometry.influences)
        self.triangles = np.append(self.triangles, geometry.triangles, 0)
        return True
        # todo bone indices

    def swap_y_z_axis(self):
        collections = [self.vertices, self.normals]
        points = self.vertices.points
        points[:, [1, 2]] = points[:, [2, 1]]
        points[:, 2] *= -1
        points = self.normals.points
        points[:, [1, 2]] = points[:, [2, 1]]

    def apply_linked_bone_bindings(self, bones):
        if self.influences is not None:
            # multiple influences
            if type(self.influences) == InfluenceCollection:
                raise NotImplementedError('Multiple influences!')
            else:
                self.apply_matrix(np.array(bones[self.influences].get_transform_matrix(), np.float))

    def apply_matrix(self, matrix):
        if matrix is not None and not np.allclose(matrix, np.identity(4)):
            self.vertices.apply_affine_matrix(matrix)

    def get_linked_bone(self):
        return self.linked_bone

    def encode(self, mdl, bone=None):
        if not bone:
            bone = self.get_linked_bone()
            if not bone:
                if not mdl.bones:
                    mdl.add_bone(mdl.name)
                self.linked_bone = bone = mdl.bones[0]
        self.linked_bone.has_geometry = True
        p = Polygon(self.name, mdl)
        fmt_str = '>'
        fmt_str += self.__encode_influences(p, self.influences, mdl)
        fmt_str += self.__encode_vertices(p, self.vertices, mdl)
        fmt_str += self.__encode_normals(p, self.normals, mdl)
        fmt_str += self.__encode_colors(p, self.colors, mdl)
        fmt_str += self.__encode_texcoords(p, self.texcoords, mdl)
        data = self.__encode_tris(p, self.__construct_tris(p), fmt_str)
        if data is None:
            # todo, cleanup?
            return data
        if p.has_pos_matrix:
            data = self.__encode_load_matrices(p.bone_table) + data
        p.vt_data = data
        mdl.add_to_group(mdl.objects, p)
        material = mdl.getMaterialByName(self.material_name)
        mdl.add_definition(material, p, bone)
        if self.colors:
            material.enable_vertex_color()
        return p

    @staticmethod
    def __encode_load_matrices_helper(data, indices, xf_address, matrix_len, cmd):
        mtx_len_shifted = matrix_len - 1 << 12
        for bone_index in indices:
            data += pack('>B', cmd)
            data += pack('>2H', bone_index, mtx_len_shifted | xf_address)
            xf_address += matrix_len

    @staticmethod
    def __encode_load_matrices(indices):
        data = bytearray()
        # pos matrices
        Geometry.__encode_load_matrices_helper(data, indices, 0, 12, 0x20)
        # normal matrices
        Geometry.__encode_load_matrices_helper(data, indices, 1024, 9, 0x28)
        return data

    @staticmethod
    def __encode_tris(polygon, tris, fmt_str):
        tris[:, [0, 1]] = tris[:, [1, 0]]
        triset = TriangleSet(tris)
        if not triset:
            return None
        data, polygon.face_count, polygon.facepoint_count = triset.get_tri_strips(fmt_str)
        past_align = len(data) % 32
        if past_align:
            data.extend(b'\0' * (32 - past_align))
        return data

    def __encode_influences(self, polygon, influences, mdl0):
        if influences is not None:
            if influences.is_mixed():
                polygon.bone_table = [i for i in range(len(mdl0.bones))]
                polygon.bone = -1
                polygon.has_pos_matrix = True
                return 'B'
            else:
                polygon.bone = self.linked_bone.index
        return ''
        # face_indices = influences.get_face_indices(vertex_face_indices)

    def __encode_vertices(self, polygon, vertices, mdl0):
        vert = Vertex(self.name, mdl0)
        mdl0.add_to_group(mdl0.vertices, vert)
        linked_bone = self.linked_bone
        rotation_matrix = get_rotation_matrix(np.array(linked_bone.get_transform_matrix(), dtype=float))
        points = vertices.points
        if polygon.has_pos_matrix:
            for i in range(len(vertices)):
                influence = self.influences[i]
                points[i] = np.dot(rotation_matrix, influence.apply_to(points[i], decode=False))
            polygon.vertex_format, polygon.vertex_divisor, remapper = vertices.encode_data(vert, True)
            if remapper is not None:
                new_inf_map = {}
                old_inf_map = self.influences.influences
                for i in old_inf_map:
                    new_inf_map[remapper[i]] = old_inf_map[i]
                self.influences.influences = new_inf_map
        else:
            for i in range(len(points)):
                points[i] = np.dot(rotation_matrix, points[i])
            inv_matrix = np.array(linked_bone.get_inv_transform_matrix(), dtype=float)
            vertices.points = apply_matrix(inv_matrix, vertices.points)
            polygon.vertex_format, polygon.vertex_divisor = vertices.encode_data(vert, False)
        polygon.vertex_group_index = vert.index
        polygon.vertex_index_format, fmt_str = get_index_format(vert)
        return fmt_str

    def __encode_normals(self, polygon, normals, mdl0):
        if normals:
            normal = Normal(self.name, mdl0)
            polygon.normal_format = normals.encode_data(normal)[0]
            mdl0.add_to_group(mdl0.normals, normal)
            polygon.normal_type = normal.comp_count
            polygon.normal_group_index = normal.index
            polygon.normal_index_format, fmt_str = get_index_format(normal)
        else:
            polygon.normal_index_format = polygon.INDEX_FORMAT_NONE
            polygon.normal_group_index = -1
            fmt_str = ''
        return fmt_str

    def __encode_colors(self, polygon, colors, mdl0):
        if colors:
            color = Color(self.name, mdl0)
            polygon.color0_format = colors.encode_data(color)
            mdl0.add_to_group(mdl0.colors, color)
            polygon.color0_index_format, fmt_str = get_index_format(color)
            polygon.color_group_indices[0] = color.index
            polygon.num_colors = 1
        else:
            polygon.color0_index_format = polygon.INDEX_FORMAT_NONE
            polygon.num_colors = 0
            polygon.color_group_indices[0] = -1
            fmt_str = ''
        return fmt_str

    def __encode_texcoords(self, polygon, texcoords, mdl0):
        fmt_str = ''
        if texcoords:
            uv_i = len(mdl0.texCoords)
            for i in range(len(texcoords)):
                x = texcoords[i]
                tex = TexCoord(self.name + '#{}'.format(i), mdl0)
                # convert xy to st
                x.flip_points()
                polygon.tex_format[i], polygon.tex_divisor[i] = x.encode_data(tex)
                tex.index = uv_i + i
                mdl0.texCoords.append(tex)
                polygon.tex_index_format[i], fmt = get_index_format(tex)
                fmt_str += fmt
                polygon.tex_coord_group_indices[i] = tex.index
        else:
            polygon.tex_coord_group_indices[0] = -1
            polygon.tex_index_format[0] = polygon.INDEX_FORMAT_NONE
        return fmt_str

    def __construct_tris(self, polygon):
        tris = []
        vert_face_indices = self.vertices.face_indices
        if polygon.has_pos_matrix:  # multiple influences?
            tris.append(self.influences.get_face_indices(vert_face_indices))
        tris.append(vert_face_indices)
        if self.normals:
            tris.append(self.normals.face_indices)
        if self.colors:
            tris.append(self.colors.face_indices)
        for texcoord in self.texcoords:
            tris.append(texcoord.face_indices)
        return np.stack(tris, -1)

    def __geometry_matches(self, geometry):
        return not (self.material_name != geometry.material_name or \
                    self.linked_bone is not geometry.linked_bone or \
                    ((self.normals is None) ^ (geometry.normals is None)) or \
                    ((self.colors is None) ^ (geometry.colors is None)) or \
                    len(self.texcoords) != len(geometry.texcoords) or \
                    self.influences != geometry.influences)


def get_index_format(item):
    l = len(item)
    if l > 0xffff:
        raise Converter.ConvertError(f'{item.name} exceeds max length! ({len(item)})')
    elif l > 0xff:
        return Polygon.INDEX_FORMAT_SHORT, 'H'
    else:
        return Polygon.INDEX_FORMAT_BYTE, 'B'


def decode_tri_strip(decoder, decoder_byte_len, data, start_offset, num_facepoints, face_point_indices):
    face_points = []
    flip = False
    for i in range(num_facepoints):
        face_points.append(unpack_from(decoder, data, start_offset))
        start_offset += decoder_byte_len
        if i >= 2:
            if flip:
                face_point_indices.append((face_points[i - 1], face_points[i - 2], face_points[i]))
            else:
                face_point_indices.append(face_points[i - 2:i + 1])
        flip = not flip
    return start_offset


def decode_tris(decoder, decoder_byte_len, data, start_offset, num_facepoints, face_point_indices):
    assert num_facepoints % 3 == 0
    for i in range(int(num_facepoints / 3)):
        tri = []
        for j in range(3):
            tri.append(unpack_from(decoder, data, start_offset))
            start_offset += decoder_byte_len
        face_point_indices.append(tri)
    return start_offset


def decode_geometry_group(geometry):
    arr = np.array(geometry.data, np.float)
    if geometry.divisor:
        arr = arr / (2 ** geometry.divisor)
    return arr


def get_stride(fmt_str):
    stride = 0
    for x in fmt_str:
        if x == 'H':
            stride += 2
        elif x == 'B':
            stride += 1
        elif x != '>':
            raise ValueError('Unknown decoder format {}'.format(x))
    return stride


def decode_indices(polygon, fmt_str):
    # now decode the indices
    face_point_indices = []
    stride = get_stride(fmt_str)
    data = polygon.vt_data
    total_face_points = i = 0
    bones = []
    face_point_count = polygon.facepoint_count
    while total_face_points < face_point_count:
        [cmd] = unpack_from('>B', data, i)
        i += 1
        if cmd in (0x98, 0x90):
            [num_facepoints] = unpack_from('>H', data, i)
            i += 2
            if cmd == 0x98:
                i = decode_tri_strip(fmt_str, stride, data, i, num_facepoints, face_point_indices)
            elif cmd == 0x90:
                i = decode_tris(fmt_str, stride, data, i, num_facepoints, face_point_indices)
            total_face_points += num_facepoints
        elif cmd in (0x20, 0x28, 0x30):  # load matrix
            bone_index, len_and_xf_address = unpack_from('>2H', data, i)
            xf_address = 0xfff & len_and_xf_address
            length = (len_and_xf_address >> 12) + 1
            i += 4
            if cmd == 0x20:  # pos matrix
                bones.append(bone_index)
            elif cmd == 0x28:
                pass  # normals  no parsing?
            elif cmd == 0x30:   # tex matrix
                pass
            else:
                raise Converter.ConvertError('Texture matrices not supported')
        else:
            raise ValueError('Unsupported draw cmd {}'.format(cmd))
    return face_point_indices, bones


def order_influences(vertex_indices, influence_indices):
    arr, indices = np.unique(vertex_indices, return_index=True)
    return influence_indices.flatten()[indices]


def apply_influences(influences, vertices, bone_transform_matrices):
    """Applies the influence [(bone_id, weight), ...] to each vertex"""
    assert len(influences) == len(vertices)
    for i in range(len(influences)):
        pass


def decode_polygon(polygon, influences):
    """ Decodes an mdl0 polygon
            :returns geometry
        """
    # build the fmt_str decoder
    fmt_str = '>'
    geometry_index = 0
    if polygon.has_pos_matrix:
        fmt_str += 'B'
        pos_matrix_index = geometry_index
        geometry_index += 1
        # raise Converter.ConvertError('{} vertex weighting not supported'.format(polygon.name))
    else:
        pos_matrix_index = -1
    tex_matrix_index = -1
    for x in polygon.has_tex_matrix:
        if not x:
            continue
        if tex_matrix_index < 0:
            tex_matrix_index = geometry_index
        fmt_str += 'B'
        geometry_index += 1
        # raise Converter.ConvertError('{} texcoord matrix not supported'.format(polygon.name))
    vertex_index = geometry_index
    geometry_index += 1
    vertices = polygon.get_vertex_group()
    fmt_str += polygon.get_fmt_str(polygon.vertex_index_format)
    normals = polygon.get_normal_group()
    if normals:
        fmt_str += polygon.get_fmt_str(polygon.normal_index_format)
        normal_index = geometry_index
        geometry_index += 1
    colors = polygon.get_color_group()
    if colors:
        fmt_str += polygon.get_fmt_str(polygon.color0_index_format)
        color_index = geometry_index
        geometry_index += 1
    texcoords = []
    texcoord_index = -1
    for i in range(polygon.num_tex):
        texcoords.append(polygon.get_tex_group(i))
        fmt_str += polygon.get_fmt_str(polygon.tex_index_format[i])
        if i == 0:
            texcoord_index = geometry_index
            geometry_index += 1

    face_point_indices, bones = decode_indices(polygon, fmt_str)
    face_point_indices = np.array(face_point_indices, dtype=np.uint)
    face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0]]
    vert_face_points = face_point_indices[:, :, vertex_index]
    decoded_verts = decode_geometry_group(vertices)
    linked_bone = polygon.get_bone()
    rotation_matrix = get_rotation_matrix(np.array(linked_bone.get_inv_transform_matrix(), dtype=float))
    if pos_matrix_index >= 0:  # apply influences to vertices
        influence_indices = face_point_indices[:, :, pos_matrix_index].flatten() // 3
        geo_infs = {}
        # get the ordered indices corresponding to vertices
        ordered = order_influences(vert_face_points, influence_indices)
        for i in range(len(decoded_verts)):
            influence = influences[ordered[i]]
            geo_infs[i] = influence
            # decoded_verts[i] = influence.apply_to(decoded_verts[i], decode=True)
            decoded_verts[i] = np.dot(influence.apply_to(decoded_verts[i], decode=True), rotation_matrix)

        influence_collection = InfluenceCollection(geo_infs)
    else:
        influence = influences[polygon.bone]  # todo need to check this
        decoded_verts = influence.apply_to_all(decoded_verts, decode=True)
        for i in range(len(decoded_verts)):
            decoded_verts[i] = np.dot(rotation_matrix, decoded_verts[i])
        influence_collection = InfluenceCollection({0: influence})
    if tex_matrix_index > 0:
        for x in polygon.has_tex_matrix:
            if x:
                indices = face_point_indices[:, :, tex_matrix_index]
                tex_matrix_index += 1

    g_verts = PointCollection(decoded_verts, vert_face_points)
    geometry = Geometry(polygon.name, polygon.get_material().name, g_verts,
                        triangles=face_point_indices[:, :, vertex_index:], influences=influence_collection,
                        linked_bone=linked_bone)
    # create the point collections
    if normals:
        geometry.normals = PointCollection(decode_geometry_group(normals), face_point_indices[:, :, normal_index])
    if colors:
        geometry.colors = ColorCollection(ColorCollection.decode_data(colors), face_point_indices[:, :, color_index])
    for tex in texcoords:
        x = decode_geometry_group(tex)
        pc = PointCollection(x, face_point_indices[:, :, texcoord_index],
                             tex.minimum, tex.maximum)
        pc.flip_points()
        geometry.texcoords.append(pc)
        texcoord_index += 1
    return geometry
