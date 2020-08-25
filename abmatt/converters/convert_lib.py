import math
from struct import pack

import numpy as np

from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex


def point_eq(x, y, compare_len):
    for i in range(compare_len):
        if x[i] != y[i]:
            return False
    return True


def encode_triangle_strip(triangle_indices, fmt_str, byte_array):
    byte_array.extend(pack('>BH', 0x98, len(triangle_indices)))
    for x in triangle_indices:
        byte_array.extend(pack(fmt_str, *x))
    return len(triangle_indices)


def encode_triangles(triangle_indices, fmt_str, byte_array):
    face_point_len = len(triangle_indices) * 3
    byte_array.extend(pack('>BH', 0x90, face_point_len))
    for x in triangle_indices:
        for y in x:
            byte_array.extend(pack(fmt_str, *y))
    return face_point_len


def compare_verts_unordered(original_verts, new_verts):
    unused = None
    used = set()
    for x in new_verts:
        if x not in original_verts:
            if unused:
                return None, unused
            unused = x
        else:
            used.add(x)
    return used, unused


def get_triangle_strips(triangle_indices, fmt_str):
    """Generates triangle encoded data using triangle indices
        :returns bytearray of triangle strips and triangle draw commands
    """
    triangle_strips = bytearray()
    disconnected_triangles = []
    strip = [tuple(x) for x in triangle_indices[0]]
    tri_count = 1  # number of triangles in the strip
    face_count = len(triangle_indices)  # total number of faces
    face_point_count = 0
    prev = {x for x in strip}
    for i in range(1, face_count):
        triangle = triangle_indices[i]
        # check if triangle is connected
        current_verts = {tuple(x) for x in triangle}
        if len(current_verts) < 3:  # Not really a triangle! Line!
            prev = {}
            face_count -= 1  # subtract from face count
            continue
        connected, disconnected_vert = compare_verts_unordered(prev, current_verts)
        if connected:
            if tri_count == 1:  # only 1 tri, so we can swap edge vertices
                for j in range(3):
                    if strip[j] not in connected:
                        if j != 0:  # swap
                            strip.insert(0, strip.pop(j))
                        break
                prev = current_verts
            elif tri_count == 2:  # 2 triangles, can swap 1 and 2
                if strip[1] in connected:
                    if strip[2] not in connected:
                        strip.insert(1, strip.pop(2))
                    else:
                        connected = None
                if connected:
                    prev = strip[-2:]
            else:  # multiple ordered triangles
                prev = strip[-2:]
        if not connected:
            if tri_count > 1:  # more than one tri?
                face_point_count += encode_triangle_strip(strip, fmt_str, triangle_strips)
                tri_count = 1
            else:
                disconnected_triangles.append(strip)
            strip = [x for x in current_verts]
            prev = current_verts
        else:
            strip.append(disconnected_vert)
            tri_count += 1

    if len(strip) > 3:
        face_point_count += encode_triangle_strip(strip, fmt_str, triangle_strips)
    else:
        disconnected_triangles.append(strip)
    # Now add on any disconnected triangles
    face_point_count += encode_triangles(disconnected_triangles, fmt_str, triangle_strips)
    return triangle_strips, face_count, face_point_count


def encode_polygon_data(polygon, vertex, normal, color, uvs, face_indices):
    # set up vertex declaration
    polygon.vertex_format = vertex.format
    polygon.vertex_divisor = vertex.divisor
    if len(vertex) > 0xff:
        polygon.vertex_index_format = polygon.INDEX_FORMAT_SHORT
        fmt_str = 'H'
    else:
        polygon.vertex_index_format = polygon.INDEX_FORMAT_BYTE
        fmt_str = 'B'
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
    data, polygon.face_count, polygon.facepoint_count = get_triangle_strips(face_indices, fmt_str)
    past_align = len(data) % 32
    if past_align:
        data.extend(b'\0' * (32 - past_align))
    polygon.vt_data = data


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
        x.encode_data(tex)
        tex.index = uv_i
        mdl0.texCoords.append(tex)
        uv_i += 1
        uvs.append(tex)
        index_groups.append(x.face_indices)
    p = Polygon(name, mdl0)
    encode_polygon_data(p, vert, normal, color, uvs, np.stack(index_groups, axis=-1))
    mdl0.add_to_group(mdl0.objects, p)
    return p


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

    def __len__(self):
        return len(self.points)

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
    def __init__(self, rgba_colors, face_indices, encode_format=5):
        """
        :param rgba_colors: [[r,g,b,a], ...]
        :param face_indices: ndarray, list of indexes for each triangle [[tri_index0, tri_index1, tri_index2], ...]
        :param encode_format: (0=rgb565|1=rgb8|2=rgb32|3=rgba4|4=rgba6|5=rgba8)
        """
        self.rgba_colors = rgba_colors
        self.face_indices = face_indices
        self.encode_format = encode_format

    def encode_data(self, color):
        form = self.encode_format
        rgba_colors = self.rgba_colors = self.consolidate()
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
    def encode_rgb565(colors):
        data = [(x[0] & 0xf8) << 8 | (x[1] & 0xfc) << 3 | x[2] >> 3 for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def encode_rgb8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>3B', x[0], x[1], x[2]))
        return data

    @staticmethod
    def encode_rgba8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>4B', *x))
        return data

    @staticmethod
    def encode_rgba4(colors):
        data = [(x[0] & 0xf0 | x[1] & 0xf) << 8 | x[2] & 0xf0 | x[3] & 0xf for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def encode_rgba6(colors):
        data = bytearray()
        tmp = [(x[0] & 0xfc) << 16 | (x[1] & 0xfc) << 10 | (x[2] & 0xfc) << 4 | x[3] >> 2 for x in colors]
        for x in tmp:
            data.extend(pack('>3B', x >> 16, x >> 8 & 0xff, x & 0xff))
        return data

    def consolidate(self):
        return consolidate_data(self.rgba_colors, self.face_indices)

    def normalize(self):
        """Normalizes data between 0-1 to 0-255"""
        self.rgba_colors = np.around(self.rgba_colors * 255).astype(np.uint8)
