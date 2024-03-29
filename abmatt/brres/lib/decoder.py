from copy import deepcopy
from struct import unpack_from

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.converters import error
from abmatt.converters.colors import ColorCollection
from abmatt.converters.influence import InfluenceCollection, Influence, Weight
from abmatt.converters.points import PointCollection


def decode_geometry_group(geometry, n_columns, flip_points=False):
    arr = np.array(geometry.data, np.float)
    if geometry.divisor:
        arr = arr / (2 ** geometry.divisor)
    if arr.shape[1] < n_columns:
        arr = np.append(arr, np.zeros((arr.shape[0], 1), np.float), axis=1)
    if flip_points:
        arr[:, -1] = arr[:, -1] * -1 + 1    # convert st to xy
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
    influences = {}
    bones = mdl0.bones
    bonetable = mdl0.bone_table
    # Get bonetable influences
    for i in range(len(bonetable)):
        index = bonetable[i]
        if index >= 0:
            bone = bones[index]
            influences[i] = Influence(bone_weights={bone.name: Weight(bone, 1)}, influence_id=i)

    # Get mixed influences
    nodemix = mdl0.NodeMix
    if nodemix is not None:
        for inf in nodemix.mixed_weights:
            weight_id = inf.weight_id
            influences[weight_id] = influence = Influence(influence_id=weight_id)
            for x in inf:
                bone = bones[bonetable[x[0]]]
                influence[bone.name] = Weight(bone, x[1])
    return InfluenceCollection(influences)


def decode_polygon(polygon, influences=None):
    """ Decodes an mdl0 polygon
            :returns geometry
        """
    # build the decoder_string decoder
    if influences is None:
        influences = polygon.parent.get_influences()
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
    g_verts = PointCollection(vertices.get_decoded(), face_point_indices[:, :, vertex_index])
    linked_bone = polygon.get_linked_bone()
    if pos_matrix_index >= 0:  # apply influences to vertices
        influence_collection = decode_pos_mtx_indices(influences, weights, g_verts,
                                                      face_point_indices[:, :, pos_matrix_index] // 3)
    else:
        influence = influences[linked_bone.weight_id]
        g_verts.apply_affine_matrix(np.array(linked_bone.get_transform_matrix()), apply=True)
        influence_collection = InfluenceCollection({0: influence})
    from abmatt.converters.geometry import Geometry
    geometry = Geometry(polygon.name, polygon.get_material().name, g_verts,
                        triangles=None, influences=influence_collection,
                        linked_bone=linked_bone)
    # create the point collections
    if normals:
        geometry.normals = PointCollection(normals.get_decoded(), face_point_indices[:, :, normal_index])
    if colors:
        geometry.colors = ColorCollection(colors.get_decoded(), face_point_indices[:, :, color_index])
    for tex in texcoords:
        pc = PointCollection(tex.get_decoded(), face_point_indices[:, :, texcoord_index],
                             tex.minimum, tex.maximum)
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

    remapper = {}
    new_points = []
    new_face_indices = deepcopy(vert_indices)
    # Each weighting slice group
    for i in range(len(slicer) - 1):
        start = slicer[i]
        end = slicer[i + 1]
        weights = np.array(weight_groups[start])
        vertex_slice = vert_indices[start:end]
        pos_mtx_slice = pos_mtx_indices[start:end]

        # map each vertex to an influence
        for i in range(len(vertex_slice)):
            for j in range(3):
                vert_id = vertex_slice[i, j]
                inf = all_influences[weights[pos_mtx_slice[i, j]]]
                weight_id = inf.influence_id
                remappings = remapper.get(vert_id)
                add_it = bool(remappings is None)
                if not remappings:
                    remapper[vert_id] = remappings = []
                if not add_it:
                    add_it = True
                    for index, influence in remappings:
                        if influence.influence_id == weight_id:
                            add_it = False
                            new_face_indices[start + i, j] = index
                            break
                if add_it:
                    remappings.append((len(new_points), inf))
                    influences[len(new_points)] = inf
                    new_face_indices[start + i, j] = len(new_points)
                    new_points.append(inf.apply_to(points[vert_id], decode=True))
    vertices.points = np.array(new_points)
    vertices.face_indices = new_face_indices
    assert len(influences) == len(new_points)
    return InfluenceCollection(influences)
