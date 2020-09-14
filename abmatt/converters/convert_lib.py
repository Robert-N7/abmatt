import math
import os
from struct import pack, unpack, unpack_from

import numpy as np

from brres.lib.autofix import AUTO_FIXER
from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex
from brres.mdl0 import material
from brres.tex0 import EncodeError
from converters.triangle import TriangleSet


class Converter:
    NoNormals = 0x1
    NoColors = 0x2
    IDENTITY_MATRIX = np.identity(4)

    class ConvertError(Exception):
        pass

    @staticmethod
    def get_mdl0_name(brres_name, model_name):
        common_models = ('course', 'map', 'vrcorn')
        for x in common_models:
            if x in brres_name or x in model_name:
                return x
        return model_name

    @staticmethod
    def set_bone_matrix(bone, matrix):
        """Untested set translation/scale/rotation with matrix"""
        bone.transform_matrix = matrix[:3]  # don't include fourth row
        bone.inverse_matrix = np.linalg.inv(matrix)[:3]
        bone.translation = matrix[:, 3][:3]
        bone.scale = (vector_magnitude(matrix[:, 0]),
                      vector_magnitude(matrix[:, 1]),
                      vector_magnitude(matrix[:, 2]))
        matrix = np.delete(matrix, 3, 0)
        matrix = np.delete(matrix, 3, 1)
        for i in range(3):
            scale_factor = bone.scale[i]
            if scale_factor != 1:
                for j in range(3):
                    matrix[j][i] = matrix[j][i] / scale_factor
        bone.rotation = rotationMatrixToEulerAngles(matrix)

    @staticmethod
    def is_identity_matrix(matrix):
        return np.allclose(matrix, Converter.IDENTITY_MATRIX)

    @staticmethod
    def try_import_texture(brres, image_path, layer_name=None):
        if not layer_name:
            layer_name = os.path.splitext(os.path.basename(image_path))[0]
        if not brres.hasTexture(layer_name):
            if os.path.exists(image_path):
                try:
                    brres.import_texture(image_path, layer_name)
                except EncodeError:
                    AUTO_FIXER.warn('WARN: Failed to encode image {}'.format(image_path))
        return layer_name

    def __init__(self, brres, mdl_file, flags=0):
        self.brres = brres
        self.mdl_file = mdl_file
        self.flags = flags

    def load_model(self, model_name):
        raise NotImplementedError()

    def save_model(self, mdl0):
        raise NotImplementedError()


def encode_polygon_data(polygon, vertex, normal, color, uvs, face_indices):
    # set up vertex declaration
    polygon.vertex_format = vertex.format
    polygon.vertex_divisor = vertex.divisor
    if len(vertex) > 0xff:
        polygon.vertex_index_format = polygon.INDEX_FORMAT_SHORT
        fmt_str = '>H'
    else:
        polygon.vertex_index_format = polygon.INDEX_FORMAT_BYTE
        fmt_str = '>B'
    polygon.facepoint_count = len(vertex)
    polygon.vertex_group_index = vertex.index
    if normal:
        polygon.normal_type = normal.comp_count
        polygon.normal_group_index = normal.index
        polygon.normal_format = normal.format
        if len(normal) > 0xff:
            polygon.normal_index_format = polygon.INDEX_FORMAT_SHORT
            fmt_str += 'H'
        else:
            polygon.normal_index_format = polygon.INDEX_FORMAT_BYTE
            fmt_str += 'B'
    else:
        polygon.normal_index_format = polygon.INDEX_FORMAT_NONE
        polygon.normal_group_index = -1
    if color:
        if len(color) > 0xff:
            polygon.color0_index_format = polygon.INDEX_FORMAT_SHORT
            fmt_str += 'H'
        else:
            polygon.color0_index_format = polygon.INDEX_FORMAT_BYTE
            fmt_str += 'B'
        polygon.color0_has_alpha = color.has_alpha
        polygon.color_group_indices[0] = color.index
    else:
        polygon.color0_index_format = polygon.INDEX_FORMAT_NONE
        polygon.num_colors = 0
    polygon.num_tex = len(uvs)
    if polygon.num_tex:
        for i in range(len(uvs)):
            uv = uvs[i]
            polygon.tex_coord_group_indices[i] = uv.index
            polygon.tex_format[i] = uv.format
            polygon.tex_divisor[i] = uv.divisor
            if len(uv) > 0xff:
                polygon.tex_index_format[i] = polygon.INDEX_FORMAT_SHORT
                fmt_str += 'H'
            else:
                polygon.tex_index_format[i] = polygon.INDEX_FORMAT_BYTE
                fmt_str += 'B'
    else:
        polygon.tex_coord_group_indices[0] = -1
    triset = TriangleSet(face_indices)
    if not triset:
        return None
    data, polygon.face_count, polygon.facepoint_count = triset.get_tri_strips(fmt_str)
    past_align = len(data) % 32
    if past_align:
        data.extend(b'\0' * (32 - past_align))
    polygon.vt_data = data
    return polygon


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
        raise Converter.ConvertError('{} vertex weighting not supported'.format(polygon.name))
        geometry_index += 1
    else:
        pos_matrix_index = -1
    tex_matrix_index = -1
    for x in polygon.has_tex_matrix:
        if x:
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
    else:
        normal_index = -1
    colors = polygon.get_color_group()
    if colors:
        fmt_str += polygon.get_fmt_str(polygon.color0_index_format)
        color_index = geometry_index
        geometry_index += 1
    else:
        color_index = -1
    texcoords = []
    texcoord_index = -1
    for i in range(polygon.num_tex):
        texcoords.append(polygon.get_tex_group(i))
        fmt_str += polygon.get_fmt_str(polygon.tex_index_format[i])
        if i == 0:
            texcoord_index = geometry_index
            geometry_index += 1
    fp_data_length = 0
    for x in fmt_str:
        if x == 'H':
            fp_data_length += 2
        elif x == 'B':
            fp_data_length += 1
        elif x != '>':
            raise ValueError('Unknown decoder format {}'.format(x))
    # now decode the indices
    face_point_indices = []
    data = polygon.vt_data
    total_face_points = i = 0
    matrix_indices = []
    face_point_count = polygon.facepoint_count
    while total_face_points < face_point_count:
        cmd, num_facepoints = unpack_from('>BH', data, i)
        i += 3
        total_face_points += num_facepoints
        if cmd == 0x98:
            i = decode_tri_strip(fmt_str, fp_data_length, data, i, num_facepoints, face_point_indices)
        elif cmd == 0x90:
            i = decode_tris(fmt_str, fp_data_length, data, i, num_facepoints, face_point_indices)
        elif cmd in (0x20, 0x28, 0x30):  # load matrix
            matrix_index = unpack_from('>2B', data, i)
            matrix_indices.append(matrix_index)
            i += 2
        else:
            raise ValueError('Unsupported draw cmd {}'.format(cmd))
    face_point_indices = np.array(face_point_indices, np.int)
    face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0]]
    # create the point collections
    g_verts = PointCollection(decode_geometry_group(vertices), face_point_indices[:, :, vertex_index],
                              vertices.minimum, vertices.maximum)
    if normals:
        g_normals = PointCollection(decode_geometry_group(normals), face_point_indices[:, :, normal_index])
    else:
        g_normals = None
    if colors:
        g_colors = ColorCollection(ColorCollection.decode_data(colors), face_point_indices[:, :, color_index])
    else:
        g_colors = None
    geo_texcoords = []
    for tex in texcoords:
        x = decode_geometry_group(tex)
        x[:, 1] *= -1  # flip y
        geo_texcoords.append(PointCollection(x, face_point_indices[:, :, texcoord_index],
                                             tex.minimum, tex.maximum))
        texcoord_index += 1
    face_point_indices = np.copy(face_point_indices[:, :, vertex_index:])
    geometry = Geometry(polygon.name, polygon.get_material().name, face_point_indices, g_verts,
                        geo_texcoords, g_normals, g_colors)
    return geometry


def add_geometry(mdl0, name, vertices, normals, colors, tex_coord_groups):
    """
    Adds the geometry, note that point collection face indices must match in size!
    :param mdl0:
    :param name: obj name
    :param vertices: point_collection
    :param normals: optional point_collection
    :param colors: optional color_collection
    :param tex_coord_groups: list of up to 8 tex coord point_collection(s)
    """
    # print('Adding geometry {}'.format(name))    # Debug
    vert = Vertex(name, mdl0)
    vertices.encode_data(vert)
    mdl0.add_to_group(mdl0.vertices, vert)
    index_groups = [vertices.face_indices]
    if normals:
        normal = Normal(name, mdl0)
        normals.encode_data(normal)
        mdl0.add_to_group(mdl0.normals, normal)
        index_groups.append(normals.face_indices)
    else:
        normal = None
    if colors:
        color = Color(name, mdl0)
        colors.encode_data(color)
        mdl0.add_to_group(mdl0.colors, color)
        index_groups.append(colors.face_indices)
    else:
        color = None
    uvs = []
    uv_i = len(mdl0.texCoords)
    for x in tex_coord_groups:
        tex = TexCoord('#{}'.format(uv_i), mdl0)
        # convert xy to st
        x.points[:, 1] *= -1
        x.encode_data(tex)
        tex.index = uv_i
        mdl0.texCoords.append(tex)
        uv_i += 1
        uvs.append(tex)
        index_groups.append(x.face_indices)
    p = Polygon(name, mdl0)
    indices = np.stack(index_groups, axis=-1)
    indices[:, [0, 1]] = indices[:, [1, 0]]
    if encode_polygon_data(p, vert, normal, color, uvs, indices):
        mdl0.add_to_group(mdl0.objects, p)
        return p
    # cleanup
    mdl0.vertices.pop(-1)
    if normals:
        mdl0.normals.pop(-1)
    if colors:
        mdl0.colors.pop(-1)
    for x in tex_coord_groups:
        mdl0.texCoords.pop(-1)


def consolidate_point_collections(point_collections):
    """Attempts to further join together collections that have already been consolidated"""
    # Track the current points that are indexed by a byte (255 max) or by short
    points_byte_indexed = None
    points_short_indexed = None
    for x in point_collections:
        c_len = len(x)
        consolidated = False
        if c_len <= 0xff:  # byte indexed
            # check if it can fit (even with no consolidation)
            if len(points_byte_indexed) + c_len <= 0xff:
                # try to consolidate
                pass
            if not consolidated and c_len < len(points_byte_indexed):
                points_byte_indexed = x.points  # start over using the smallest size
        else:  # short indexed
            if len(points_short_indexed) + c_len <= 0xffff:
                pass
            if not consolidated and c_len < len(points_short_indexed):
                points_short_indexed = x.points  # start over using the smallest size


def consolidate_data(points, face_indices):
    point_index_map = {}  # maps points to index
    index_remapper = {}  # map original indexes to new
    new_index = 0
    new_points = []
    point_len = len(points)
    # First consolidate and map point indices
    for original_index in range(point_len):
        x = points[original_index]
        y = tuple(x)
        point_index = point_index_map.get(y)
        if not point_index:  # add
            point_index_map[y] = new_index
            index_remapper[original_index] = new_index
            new_points.append(y)
            new_index += 1
        else:
            index_remapper[original_index] = point_index
    if len(new_points) >= point_len:  # No gain
        return points
    points = np.array(new_points, points.dtype)
    # Next, update the face indices
    face_height = len(face_indices)
    face_width = len(face_indices[0])
    for i in range(face_height):
        x = face_indices[i]
        for j in range(face_width):
            x[j] = index_remapper[x[j]]
    return points


class PointCollection:

    def __init__(self, points, face_indices, minimum=None, maximum=None):
        """
        :param points: 2-d numpy array of points
        :param face_indices: ndarray of triangle indices, indexing points
        :param minimum: the minimum value
        :param maximum: the maximum value
        """
        self.points = points
        self.face_indices = face_indices
        width = len(points[0])
        if not minimum or not maximum:
            minimum = [math.inf] * width
            maximum = [-math.inf] * width
            for x in points:
                for i in range(width):
                    if x[i] < minimum[i]:
                        minimum[i] = x[i]
                    if x[i] > maximum[i]:
                        maximum[i] = x[i]
        self.minimum = minimum
        self.maximum = maximum

    def __iter__(self):
        return iter(self.points)

    def __next__(self):
        return next(self.points)

    def __len__(self):
        return len(self.points)

    def get_stride(self):
        return len(self.points[0])

    @staticmethod
    def get_format_divisor(minimum, maximum):
        point_max = max(maximum)
        point_min = min(minimum)
        is_signed = True if point_min < 0 else False
        point_max = max(point_max, abs(point_min))
        maxi = 0xffff if not is_signed else 0x7fff
        max_shift = 0
        while point_max < maxi and max_shift < 16:
            point_max *= 2
            max_shift += 1
        max_shift -= 1
        if max_shift <= 5:  # guarantee 5 decimals of precision
            return 4, 0  # float
        return 0x2 + is_signed, max_shift  # short

    def encode_data(self, geometry):
        """Encodes the point collection as geometry data, returns the data width (component count)
        :type geometry: Geometry
        :type self: PointCollection
        """
        geometry.minimum = self.minimum
        geometry.maximum = self.maximum
        form, divisor = self.get_format_divisor(self.minimum, self.maximum)
        points = self.points
        point_width = len(points[0])
        if form == 4:
            geometry.stride = point_width * 4
        elif form > 1:
            geometry.stride = point_width * 2
        else:
            geometry.stride = point_width
        geometry.comp_count = geometry.COMP_COUNT.index(point_width)
        geometry.format = form
        geometry.divisor = divisor
        multiplyBy = 2 ** divisor
        data = geometry.data
        if divisor:
            dtype = np.int16 if form == 3 else np.uint16
            self.encode_points(multiplyBy, dtype)
        points = self.consolidate_points()
        geometry.count = len(self)
        for x in points:
            data.append(x)
        return data

    def consolidate_points(self, precision=None):
        points = self.points if not precision else np.around(self.points, precision)
        self.points = consolidate_data(points, self.face_indices)
        return self.points

    def encode_points(self, multiplier, dtype):
        x = np.around(self.points * multiplier)
        self.points = x.astype(dtype)


class ColorCollection:

    def __init__(self, rgba_colors, face_indices, encode_format=None, normalize=False):
        """
        :param rgba_colors: [[r,g,b,a], ...] between 0-1, normalizes to 0-255
        :param face_indices: ndarray, list of indexes for each triangle [[tri_index0, tri_index1, tri_index2], ...]
        :param encode_format: (0=rgb565|1=rgb8|2=rgb32|3=rgba4|4=rgba6|5=rgba8)
        """
        self.rgba_colors = rgba_colors
        if normalize:
            self.normalize()
        self.face_indices = face_indices
        self.encode_format = encode_format

    def get_encode_format(self):
        if (self.rgba_colors[:, 3] == 255).all():
            return 1
        return 5

    def encode_data(self, color):
        rgba_colors = self.rgba_colors = self.consolidate()
        form = self.encode_format if self.encode_format is not None else self.get_encode_format()
        color.format = form
        if form < 3:
            color.stride = form + 2
            color.has_alpha = False
        else:
            color.has_alpha = True
            color.stride = form - 1
        color.count = len(rgba_colors)
        if form == 0:
            color.data = self.encode_rgb565(rgba_colors)
        elif form == 1:
            color.data = self.encode_rgb8(rgba_colors)
        elif form == 2 or form == 5:
            color.data = self.encode_rgba8(rgba_colors)
        elif form == 3:
            color.data = self.encode_rgba4(rgba_colors)
        elif form == 4:
            color.data = self.encode_rgba6(rgba_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return color.data

    @staticmethod
    def decode_data(color):
        form = color.format
        num_colors = len(color)
        data = color.data
        if form == 0:
            data = ColorCollection.decode_rgb565(data, num_colors)
        elif form == 1:
            data = ColorCollection.decode_rgb8(data, num_colors)
        elif form == 2 or form == 5:
            data = ColorCollection.decode_rgba8(data, num_colors)
            if form == 2:
                data[:][3] = 0xff
        elif form == 3:
            data = ColorCollection.decode_rgba4(data, num_colors)
        elif form == 4:
            data = ColorCollection.decode_rgba6(data, num_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return np.array(data, np.uint8)

    @staticmethod
    def encode_rgb565(colors):
        data = [(x[0] & 0xf8) << 8 | (x[1] & 0xfc) << 3 | x[2] >> 3 for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def decode_rgb565(color_data, num_colors):
        data = unpack('>{}H'.format(num_colors), color_data)
        colors = []
        for color in data:
            colors.append(((color >> 8) & 0xf8, (color >> 3) & 0xfc, (color & 0x1f) << 3, 0xff))
        return colors

    @staticmethod
    def encode_rgb8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>3B', x[0], x[1], x[2]))
        return data

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
    def encode_rgba8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>4B', *x))
        return data

    @staticmethod
    def decode_rgba8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            colors.append(unpack_from('>4B', data, offset))
            offset += 4
        return colors

    @staticmethod
    def encode_rgba4(colors):
        data = [(x[0] & 0xf0 | x[1] & 0xf) << 8 | x[2] & 0xf0 | x[3] & 0xf for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def decode_rgba4(data, num_colors):
        colors = []
        c_data = unpack('>{}H'.format(num_colors), data)
        for color in c_data:
            colors.append((color >> 8 & 0xf0, color >> 4 & 0xf0,
                           color & 0xf0, color << 4 & 0xf0))
        return colors

    @staticmethod
    def encode_rgba6(colors):
        data = bytearray()
        tmp = [(x[0] & 0xfc) << 16 | (x[1] & 0xfc) << 10 | (x[2] & 0xfc) << 4 | x[3] >> 2 for x in colors]
        for x in tmp:
            data.extend(pack('>3B', x >> 16, x >> 8 & 0xff, x & 0xff))
        return data

    @staticmethod
    def decode_rgba6(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            d = unpack_from('>3B', data, offset)
            colors.append((d[0] & 0xfc, (d[0] & 0x3) << 6 | (d[1] & 0xf0) >> 2,
                           d[1] << 4 & 0xf0 | d[2] >> 4 & 0xc, d[2] << 2 & 0xfc))
            offset += 3
        return colors

    def consolidate(self):
        return consolidate_data(self.rgba_colors, self.face_indices)

    def normalize(self):
        """Normalizes data between 0-1 to 0-255"""
        self.rgba_colors = np.around(self.rgba_colors * 255).astype(np.uint8)

    def denormalize(self):
        """Opposite of normalize. returns ndarray converted from 0-255 to 0-1"""
        return self.rgba_colors.astype(np.float) / 255


class Geometry:
    def __init__(self, name, material_name, triangles, vertices, texcoords, normals=None, colors=None):
        self.name = name
        self.triangles = triangles
        self.vertices = vertices
        self.texcoords = texcoords
        self.normals = normals
        self.colors = colors
        self.material_name = material_name

    def swap_y_z_axis(self):
        # self.triangles[:, [1, 2]] = self.triangles[:, [2, 1]]
        collections = [self.vertices, self.normals]
        points = self.vertices.points
        points[:, [1, 2]] = points[:, [2, 1]]
        points[:, 2] *= -1
        points = self.normals.points
        points[:, [1, 2]] = points[:, [2, 1]]


    def encode(self, mdl, bone=None):
        polygon = add_geometry(mdl, self.name, self.vertices, self.normals, self.colors, self.texcoords)
        if polygon:
            if not bone:
                if not mdl.bones:
                    mdl.add_bone(mdl.name)
                bone = mdl.bones[0]
            material = mdl.getMaterialByName(self.material_name)
            mdl.add_definition(material, polygon, bone)
            if self.colors:
                material.enable_vertex_color()
        return polygon


class Material:
    def __init__(self, name, diffuse_map=None, ambient_map=None, specular_map=None, transparency=0):
        self.name = name
        self.ambient_map = ambient_map
        self.diffuse_map = diffuse_map
        self.specular_map = specular_map
        self.transparency = transparency

    def get_maps(self):
        maps = set()
        maps.add(self.ambient_map)
        maps.add(self.diffuse_map)
        maps.add(self.specular_map)
        if None in maps:
            maps.remove(None)
        return maps

    @staticmethod
    def encode_map(map, material):
        if map:
            layer_name = os.path.splitext(os.path.basename(map))[0]
            material.addLayer(layer_name)

    def encode(self, mdl):
        m = material.Material.get_unique_material(self.name, mdl)
        mdl.add_material(m)
        if self.transparency > 0:
            m.enable_blend()
        # maps
        self.encode_map(self.diffuse_map, m)
        self.encode_map(self.ambient_map, m)
        self.encode_map(self.specular_map, m)
        return m


class Controller:
    def __init__(self, name, bind_shape_matrix, bones, weights, vertex_weight_counts, vertex_weight_indices,
                 geometry):
        self.name = name
        self.bind_shape_matrix = bind_shape_matrix
        self.bones = bones
        self.weights = weights
        self.vertex_weight_counts = vertex_weight_counts
        self.vertex_weight_indices = vertex_weight_indices
        self.geometry = geometry

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) ==  1.0


def get_default_controller(geometry, bone_names):
    vert_len = len(geometry.vertices)
    bind_matrix = np.eye(4)
    weights = np.array([1])
    weight_indices = np.full((vert_len, 2), 0, np.uint)
    # weight_indices = np.stack((np.zeros(vert_len, dtype=int), np.arange(1, vert_len + 1, dtype=int)), -1)
    return Controller(geometry.name, bind_matrix, bone_names, weights,
                      np.full(vert_len, 1, dtype=int), weight_indices, geometry)


def vector_magnitude(vector):
    return math.sqrt(sum(x ** 2 for x in vector))


# Checks if a matrix is a valid rotation matrix.
def isRotationMatrix(R):
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


# Calculates rotation matrix to euler angles
# The result is the same as MATLAB except the order
# of the euler angles ( x and z are swapped ).
def rotationMatrixToEulerAngles(R):
    assert (isRotationMatrix(R))

    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[2, 1], R[2, 2])
        y = math.atan2(-R[2, 0], sy)
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        y = math.atan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z]) * 180 / math.pi


def scaleMatrix(matrix, scale):
    for i in range(len(scale)):
        matrix[i][i] *= scale[i]
