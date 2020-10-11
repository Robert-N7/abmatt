from struct import unpack_from, pack

import numpy as np

from autofix import AutoFix
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
        if self.triangles is not None and geometry.triangles is not None:
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
        self.influences.apply_world_position(self.vertices)

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
        tris = self.__construct_tris()
        if p.has_pos_matrix:
            data, p.face_count, p.facepoint_count = self.__encode_weighted_tris(tris, fmt_str)
        else:
            data, p.face_count, p.facepoint_count = self.__encode_tris(tris, fmt_str)
        if p.face_count <= 0:
            # todo, cleanup?
            return data
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

    def __encode_weighted_tris(self, tris, fmt_str):
        data = bytearray()
        total_facepoint_count = total_face_count = 0
        # first get the weighted groups
        weighted_groups = self.influences.get_weighted_tri_groups(tris)
        for group in weighted_groups:
            # now get the matrices and face points, encode them for each group
            matrices, face_points = group.get_influence_indices()
            data.extend(self.__encode_load_matrices(matrices))
            new_data, face_count, facepoint_count = self.__encode_tris(face_points, fmt_str)
            if face_count > 0:
                total_face_count += face_count
                total_facepoint_count += facepoint_count
                data.extend(new_data)
        return data, total_face_count, total_facepoint_count

    @staticmethod
    def __encode_tris(tris, fmt_str, is_weighted=False):
        tris[:, [0, 1]] = tris[:, [1, 0]]
        triset = TriangleSet(tris, is_weighted)
        if not triset:
            return None, 0, 0
        data, face_count, facepoint_count = triset.get_tri_strips(fmt_str)
        return data, face_count, facepoint_count

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
        points = vertices.points
        if polygon.has_pos_matrix:
            AutoFix.get().warn(f'Polygon weighting is experimental, {polygon.name} will likely be incorrect.')
            for i in range(len(vertices)):
                influence = self.influences[i]
                points[i] = influence.apply_to(points[i], decode=False)
            polygon.vertex_format, polygon.vertex_divisor, remapper = vertices.encode_data(vert, True)
            if remapper is not None:
                new_inf_map = {}
                old_inf_map = self.influences.influences
                for i in old_inf_map:
                    new_inf_map[remapper[i]] = old_inf_map[i]
                self.influences.influences = new_inf_map
        else:
            rotation_matrix = get_rotation_matrix(np.array(linked_bone.get_transform_matrix(), dtype=float))
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
            polygon.num_tex = len(texcoords)
            for i in range(polygon.num_tex):
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
        tris = []
        vert_face_indices = self.vertices.face_indices
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


def get_stride(decoder_string):
    stride = 0
    for x in decoder_string:
        if x == 'H':
            stride += 2
        elif x == 'B':
            stride += 1
        elif x != '>':
            raise ValueError('Unknown decoder format {}'.format(x))
    return stride


def decode_indices(polygon, fmt_str):
    """Given a polygon and decoder string, decode the facepoint indices
        :return (face_point_indices, weight_groups)
        weight_groups is a map of the face_point index to a list of weight indices (matrices loaded)
    """
    # now decode the indices
    face_point_indices = []
    stride = get_stride(fmt_str)
    data = polygon.vt_data
    total_face_points = i = 0
    weight_groups = {}
    new_weight_group = True
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
            new_weight_group = True
        elif cmd in (0x20, 0x28, 0x30):  # load matrix
            if new_weight_group:
                weight_groups[len(face_point_indices)] = weights = []
                new_weight_group = False
            bone_index, len_and_xf_address = unpack_from('>2H', data, i)
            xf_address = 0xfff & len_and_xf_address
            # length = (len_and_xf_address >> 12) + 1
            i += 4
            if cmd == 0x20:  # pos matrix
                index = xf_address // 12
                if index == len(weights):
                    weights.append(bone_index)
                elif index < len(weights):
                    weights[index] = bone_index
            elif cmd == 0x28:
                pass  # normals  no parsing?
            elif cmd == 0x30:  # tex matrix
                pass
            else:
                raise Converter.ConvertError('Texture matrices not supported')
        else:
            raise ValueError('Unsupported draw cmd {}'.format(cmd))
    return face_point_indices, weight_groups


def decode_pos_mtx_indices(all_influences, weight_groups, vertices, pos_mtx_indices):
    """ Finds and applies the weight matrix to the corresponding vertices
    :param all_influences: map of influence ids to influences
    :param weight_groups: map of each beginning group face_point index to list of weights
    :param vertices: PointCollection
    :param pos_mtx_indices: np array of face_point indices corresponding to those in vertices
    :return: InfluenceCollection
    """
    influences = {}     # map vertex indices to influences used by this geometry
    vert_indices = vertices.face_indices
    points = vertices.points
    # Order the indices of each group so we can slice up the indices
    slicer = sorted(weight_groups.keys())
    slicer.append(len(vert_indices))  # add the max onto the end for slicing

    # Each weighting slice group
    for i in range(len(slicer) - 1):
        start = slicer[i]
        end = slicer[i + 1]
        weights = np.array(weight_groups[start])
        vertex_slice = vert_indices[start:end].flatten()
        pos_mtx_slice = pos_mtx_indices[start:end].flatten()
        # get the ordered indices corresponding to vertices
        vertex_indices, indices = np.unique(vertex_slice, return_index=True)
        weight_indices = weights[pos_mtx_slice[indices]]   # get the matrix corresponding to vert index, resolve to weight_id

        # map each vertex id to an influence and apply it
        for i in range(len(vertex_indices)):
            vertex_index = vertex_indices[i]
            if vertex_index not in influences:
                influences[vertex_index] = influence = all_influences[weight_indices[i]]
                points[vertex_index] = influence.apply_to(points[vertex_index], decode=True)
            elif influences[vertex_index].influence_id != weight_indices[i]:
                AutoFix.get().warn(f'vertex {vertex_index} has multiple different influences!')
                influences[vertex_index] = all_influences[weight_indices[i]]

    assert len(influences) == len(points)
    return InfluenceCollection(influences)


def decode_polygon(polygon, influences):
    """ Decodes an mdl0 polygon
            :returns geometry
        """
    # build the decoder_string decoder
    decoder_string = '>'
    geometry_index = 0
    if polygon.has_pos_matrix:
        decoder_string += 'B'
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
        decoder_string += 'B'
        geometry_index += 1
        # raise Converter.ConvertError('{} texcoord matrix not supported'.format(polygon.name))
    vertex_index = geometry_index
    geometry_index += 1
    vertices = polygon.get_vertex_group()
    decoder_string += polygon.get_fmt_str(polygon.vertex_index_format)
    normals = polygon.get_normal_group()
    if normals:
        decoder_string += polygon.get_fmt_str(polygon.normal_index_format)
        normal_index = geometry_index
        geometry_index += 1
    colors = polygon.get_color_group()
    if colors:
        decoder_string += polygon.get_fmt_str(polygon.color0_index_format)
        color_index = geometry_index
        geometry_index += 1
    texcoords = []
    texcoord_index = -1
    for i in range(polygon.num_tex):
        texcoords.append(polygon.get_tex_group(i))
        decoder_string += polygon.get_fmt_str(polygon.tex_index_format[i])
        if i == 0:
            texcoord_index = geometry_index
            geometry_index += 1

    face_point_indices, weights = decode_indices(polygon, decoder_string)
    face_point_indices = np.array(face_point_indices, dtype=np.uint)
    face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0]]
    # decoded_verts =
    g_verts = PointCollection(decode_geometry_group(vertices), face_point_indices[:, :, vertex_index])
    linked_bone = polygon.get_bone()
    if pos_matrix_index >= 0:  # apply influences to vertices
        influence_collection = decode_pos_mtx_indices(influences, weights, g_verts,
                                                      face_point_indices[:, :, pos_matrix_index] // 3)
    else:
        influence = influences[linked_bone.weight_id]
        rotation_matrix = get_rotation_matrix(np.array(linked_bone.get_inv_transform_matrix(), dtype=float))
        decoded_verts = influence.apply_to_all(g_verts.points, decode=True)
        if not np.allclose(rotation_matrix, np.identity(3)):
            for i in range(len(decoded_verts)):
                decoded_verts[i] = np.dot(rotation_matrix, decoded_verts[i])
        influence_collection = InfluenceCollection({0: influence})
    if tex_matrix_index > 0:
        for x in polygon.has_tex_matrix:
            if x:
                indices = face_point_indices[:, :, tex_matrix_index]
                tex_matrix_index += 1

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
