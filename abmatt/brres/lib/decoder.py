from struct import unpack_from, unpack

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.converters import error
from abmatt.converters.colors import ColorCollection
from abmatt.converters.influence import InfluenceCollection, Influence, Weight
from abmatt.converters.points import PointCollection


def decode_geometry_group(geometry):
    arr = np.array(geometry.data, np.float)
    if geometry.divisor:
        arr = arr / (2 ** geometry.divisor)
    return arr


class ColorDecoder:
    @staticmethod
    def decode_data(color):
        form = color.format
        num_colors = len(color)
        data = color.data
        if form == 0:
            data = ColorDecoder.decode_rgb565(data, num_colors)
        elif form == 1:
            data = ColorDecoder.decode_rgb8(data, num_colors)
        elif form == 2 or form == 5:
            data = ColorDecoder.decode_rgba8(data, num_colors)
            if form == 2:
                data[:, 3] = 0xff
        elif form == 3:
            data = ColorDecoder.decode_rgba4(data, num_colors)
        elif form == 4:
            data = ColorDecoder.decode_rgba6(data, num_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return np.array(data, np.uint8)

    @staticmethod
    def decode_rgb565(color_data, num_colors):
        data = unpack_from('>{}H'.format(num_colors), color_data, 0)
        colors = []
        for color in data:
            colors.append(((color >> 8) & 0xf8 | 0x7, (color >> 3) & 0xfc | 0x3, (color & 0x1f) << 3 | 0x7, 0xff))
        return colors

    @staticmethod
    def decode_rgb8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            c = list(unpack_from('>3B', data, offset))
            c.append(0xff)
            colors.append(c)
            offset += 3
        return colors

    @staticmethod
    def decode_rgba8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            colors.append(unpack_from('>4B', data, offset))
            offset += 4
        return colors

    @staticmethod
    def decode_rgba4(data, num_colors):
        colors = []
        c_data = unpack_from('>{}H'.format(num_colors), data, 0)
        for color in c_data:
            colors.append((color >> 8 & 0xf0 | 0xf, color >> 4 & 0xf0 | 0xf,
                           color & 0xf0 | 0xf, color << 4 & 0xf0 | 0xf))
        return colors

    @staticmethod
    def decode_rgba6(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            d = unpack_from('>3B', data, offset)
            colors.append((d[0] & 0xfc | 0x3, (d[0] & 0x3) << 6 | (d[1] & 0xf0) >> 2 | 0x3,
                           d[1] << 4 & 0xf0 | d[2] >> 4 & 0xc | 0x3, d[2] << 2 & 0xfc | 0x3))
            offset += 3
        return colors


def decode_mdl0_influences(mdl0):
    if mdl0.influences is not None:
        return mdl0.influences
    influences = {}
    bones = mdl0.bones
    bonetable = mdl0.bone_table
    # Get bonetable influences
    for i in range(len(bonetable)):
        index = bonetable[i]
        if index >= 0:
            bone = bones[index]
            influences[i] = Influence(bone_weights={bone.name: Weight(bone, 1)}, influence_id=index)

    # Get mixed influences
    nodemix = mdl0.NodeMix
    if nodemix is not None:
        for inf in nodemix.mixed_weights:
            weight_id = inf.weight_id
            influences[weight_id] = influence = Influence(influence_id=weight_id)
            for x in inf:
                bone = bones[bonetable[x[0]]]
                influence[bone.name] = Weight(bone, x[1])
    mdl0.influences = InfluenceCollection(influences)
    return mdl0.influences


def decode_polygon(polygon, influences=None):
    """ Decodes an mdl0 polygon
            :returns geometry
        """
    # build the decoder_string decoder
    if influences is None:
        influences = decode_mdl0_influences(polygon.parent)
    pos_matrix_index = polygon.get_weight_index()
    vertex_index = polygon.get_vertex_index()
    vertices = polygon.get_vertex_group()
    normals = polygon.get_normal_group()
    normal_index = polygon.get_normal_index()
    colors = polygon.get_color_group()
    color_index = polygon.get_color0_index()
    texcoords = []
    texcoord_index = polygon.get_uv_index(0)
    for i in range(polygon.count_uvs()):
        texcoords.append(polygon.get_uv_group(i))

    face_point_indices, weights = decode_indices(polygon, polygon.encode_str)
    face_point_indices = np.array(face_point_indices, dtype=np.uint)
    face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0]]
    # decoded_verts =
    g_verts = PointCollection(decode_geometry_group(vertices), face_point_indices[:, :, vertex_index])
    linked_bone = polygon.get_linked_bone()
    if pos_matrix_index >= 0:  # apply influences to vertices
        influence_collection = decode_pos_mtx_indices(influences, weights, g_verts,
                                                      face_point_indices[:, :, pos_matrix_index] // 3)
    else:
        influence = influences[linked_bone.weight_id]
        g_verts.apply_affine_matrix(np.array(linked_bone.get_transform_matrix()), apply=True)
        influence_collection = InfluenceCollection({0: influence})
    # for x in polygon.uv_mtx_indices:
    #     if x >= 0:
    #         AutoFix.warn('{} uv matrices data lost in export.'.format(polygon.name))
    #         indices = face_point_indices[:, :, x] // 3
    #         if (indices < 10).any():
    #             print('Less than 10!')
    from abmatt.converters.geometry import Geometry
    geometry = Geometry(polygon.name, polygon.get_material().name, g_verts,
                        triangles=None, influences=influence_collection,
                        linked_bone=linked_bone)
    # create the point collections
    if normals:
        geometry.normals = PointCollection(decode_geometry_group(normals), face_point_indices[:, :, normal_index])
    if colors:
        geometry.colors = ColorCollection(ColorDecoder.decode_data(colors), face_point_indices[:, :, color_index])
    for tex in texcoords:
        x = decode_geometry_group(tex)
        pc = PointCollection(x, face_point_indices[:, :, texcoord_index],
                             tex.minimum, tex.maximum)
        pc.flip_points()
        geometry.texcoords.append(pc)
        texcoord_index += 1
    return geometry


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


def decode_indices(polygon, fmt_str):
    """Given a polygon and decoder string, decode the facepoint indices
        :return (face_point_indices, weight_groups)
        weight_groups is a map of the face_point index to a list of weight indices (matrices loaded)
    """
    # now decode the indices
    face_point_indices = []
    stride = get_stride(fmt_str)
    data = polygon.data
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
            # length = (len_and_xf_address >> 12) + 1     # 12 (matrix len)
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
                raise error.ConvertError('Texture matrices not supported')
        elif cmd == 0x00:
            AutoFix.warn('Finished parsing {} indices early, possible bug?'.format(polygon.name))
            break
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
    influences = {}  # map vertex indices to influences used by this geometry
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
        weight_indices = weights[
            pos_mtx_slice[indices]]  # get the matrix corresponding to vert index, resolve to weight_id

        # map each vertex id to an influence and apply it
        for i in range(len(vertex_indices)):
            vertex_index = vertex_indices[i]
            if vertex_index not in influences:
                influences[vertex_index] = influence = all_influences[weight_indices[i]]
                points[vertex_index] = influence.apply_to(points[vertex_index], decode=True)
            elif influences[vertex_index].influence_id != weight_indices[i]:
                AutoFix.warn(f'vertex {vertex_index} has multiple different influences!')
                influences[vertex_index] = all_influences[weight_indices[i]]

    # assert len(influences) == len(points)
    return InfluenceCollection(influences)
