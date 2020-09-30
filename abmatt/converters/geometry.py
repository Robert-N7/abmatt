from struct import unpack_from

import numpy as np

from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex
from converters.colors import ColorCollection
from converters.convert_lib import Converter
from converters.points import PointCollection
from converters.triangle import TriangleSet


class Geometry:
    def __init__(self, name, material_name, vertices, texcoords=None, normals=None, colors=None, triangles=None,
                 bones=None, bone_indices=None, linked_bone=None):
        self.name = name
        self.vertices = vertices
        if texcoords is None:
            self.texcoords = []
        else:
            self.texcoords = texcoords
        self.normals = normals
        self.colors = colors
        self.material_name = material_name
        self.bones = bones
        self.bone_indices = bone_indices
        self.linked_bone = linked_bone
        self.triangles = triangles

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

    def apply_linked_bone_bindings(self):
        self.apply_matrix(np.array(self.linked_bone.get_transform_matrix(), np.float))

    def apply_matrix(self, matrix):
        if matrix is not None and not np.allclose(matrix, np.identity(4)):
            self.vertices.apply_affine_matrix(matrix)

    def encode(self, mdl, bone=None):
        p = Polygon(self.name, mdl)
        fmt_str = '>'
        fmt_str += self.__encode_vertices(p, self.vertices, mdl)
        fmt_str += self.__encode_normals(p, self.normals, mdl)
        fmt_str += self.__encode_colors(p, self.colors, mdl)
        fmt_str += self.__encode_texcoords(p, self.texcoords, mdl)
        if self.__encode_tris(p, self.__construct_tris(), fmt_str):
            mdl.add_to_group(mdl.objects, p)
            if not bone:
                bone = self.linked_bone
                if not bone:
                    if not mdl.bones:
                        mdl.add_bone(mdl.name)
                    bone = mdl.bones[0]
            material = mdl.getMaterialByName(self.material_name)
            mdl.add_definition(material, p, bone)
            if self.colors:
                material.enable_vertex_color()
        return p

    @staticmethod
    def __encode_tris(polygon, tris, fmt_str):
        tris[:, [0, 1]] = tris[:, [1, 0]]
        triset = TriangleSet(tris)
        if not triset:
            return False
        data, polygon.face_count, polygon.facepoint_count = triset.get_tri_strips(fmt_str)
        past_align = len(data) % 32
        if past_align:
            data.extend(b'\0' * (32 - past_align))
        polygon.vt_data = data
        return True

    def __encode_vertices(self, polygon, vertices, mdl0):
        vert = Vertex(self.name, mdl0)
        mdl0.add_to_group(mdl0.vertices, vert)
        polygon.vertex_format, polygon.vertex_divisor = vertices.encode_data(vert)
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

    def __construct_tris(self):
        tris = [self.vertices.face_indices]
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
                    len(self.texcoords) != len(geometry.texcoords))


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
                pass  # normals  todo figure out how these work
            else:
                raise Converter.ConvertError('Texture matrices not supported')
        else:
            raise ValueError('Unsupported draw cmd {}'.format(cmd))
    return face_point_indices


def decode_polygon(polygon):
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
                break
            fmt_str += 'B'
            if tex_matrix_index < 0:
                tex_matrix_index = geometry_index
            geometry_index += 1
            raise Converter.ConvertError('{} texcoord matrix not supported'.format(polygon.name))
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

        face_point_indices = np.array(decode_indices(polygon, fmt_str), np.uint)
        face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0], vertex_index:]
        # face_point_indices = np.copy(face_point_indices[:, :, vertex_index:])

        # create the point collections
        g_verts = PointCollection(decode_geometry_group(vertices), face_point_indices[:, :, vertex_index],
                                  vertices.minimum, vertices.maximum)
        geometry = Geometry(polygon.name, polygon.get_material().name, g_verts,
                            triangles=face_point_indices, linked_bone=polygon.get_linked_bone())
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
        mdl0_bones = polygon.parent.bones
        # if pos_matrix_index >= 0:       # this won't get executed
            # possibly need to do something different here
            # pos_matrix_indices = face_point_indices[:, :, 0] / 3
            # bone_table = polygon.get_bone_table()
            # geometry.bones = [mdl0_bones[bone_table[i]] for i in mdl0_bones]
        # else:
        #     pos_matrix_indices = None
        #     geometry.bones = [mdl0_bones[polygon.get_bone()]]
        return geometry
