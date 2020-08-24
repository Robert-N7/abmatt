import math
from struct import pack

import numpy as np

from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex


def encode_uv_data(texcoord, point_collection):
    comp_count = encode_data(texcoord, point_collection)
    if comp_count > 2:
        raise ValueError('component count {} for tex coordinate {} out of range'.format(comp_count, texcoord.name))
    texcoord.comp_count = comp_count - 1


def encode_normal_data(normal, point_collection):
    comp_count = encode_data(normal, point_collection)
    # comp count has to be set manually if it's 0x2 (normal or binormal or tangent) since it's also 3 width
    if comp_count == 3:
        normal.comp_count = 0
    elif comp_count == 9:
        normal.comp_count = 1
    else:
        raise ValueError('Component count {} for normal {} out of range'.format(comp_count, normal.name))


def encode_vertex_data(vertex, point_collection):
    comp_count = encode_data(vertex, point_collection)
    if comp_count == 2:
        vertex.comp_count = 0  # xy position
    elif comp_count == 3:
        vertex.comp_count = 1  # xyz
    else:
        raise ValueError('Component count {} for vertex {} out of range.'.format(comp_count, vertex.name))


def point_eq(x, y, compare_len):
    for i in range(compare_len):
        if x[i] != y[i]:
            return False
    return True


def encode_data(geometry, point_collection):
    """Encodes the point collection as geometry data, returns the data width (component count)
    :type geometry: Geometry
    :type point_collection: PointCollection
    """
    geometry.minimum = point_collection.minimum
    geometry.maximum = point_collection.maximum
    form, divisor = get_format_divisor(point_collection.minimum, point_collection.maximum)
    points = point_collection.points
    point_width = len(points[0])
    fmt_str = '>'
    if form == 4:
        geometry.stride = point_width * 4
        fmt_str += '{}f'.format(point_width)
    elif form > 1:
        geometry.stride = point_width * 2
        t_str = 'H' if form == 2 else 'h'
        fmt_str += str(point_width) + t_str
    else:
        geometry.stride = point_width
        t_str = 'B' if form == 0 else 'b'
        fmt_str += str(point_width) + t_str
    geometry.format = form
    geometry.divisor = divisor
    multiplyBy = 2 ** divisor
    data = bytearray()
    if divisor:
        dtype = np.int16 if form == 3 else np.uint16
        point_collection.encode_points(multiplyBy, dtype)
    points = point_collection.consolidate_points()
    geometry.count = len(points)
    for x in points:
        data.extend(pack(fmt_str, *x))
    geometry.data = data
    return point_width


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


def encode_triangle_strip(triangle_indices, fmt_str, byte_array):
    byte_array.extend(pack('>BH', 0x98, len(triangle_indices)))
    for x in triangle_indices:
        byte_array.extend(pack(fmt_str, *x))
    return byte_array


def encode_triangles(triangle_indices, fmt_str, byte_array):
    byte_array.extend(pack('>BH', 0x90, len(triangle_indices) * 3))
    for x in triangle_indices:
        for y in x:
            byte_array.extend(pack(fmt_str, *y))
    return byte_array


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
    prev = {x for x in strip}
    for i in range(1, len(triangle_indices)):
        triangle = triangle_indices[i]
        # check if triangle is connected
        current_verts = {tuple(x) for x in triangle}
        if len(current_verts) < 3:  # Not really a triangle! Line!
            prev = {}
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
                encode_triangle_strip(strip, fmt_str, triangle_strips)
                tri_count = 1
            else:
                disconnected_triangles.append(strip)
            strip = [x for x in current_verts]
            prev = current_verts
        else:
            strip.append(disconnected_vert)
            tri_count += 1

    if len(strip) > 3:
        encode_triangle_strip(strip, fmt_str, triangle_strips)
    else:
        disconnected_triangles.append(strip)
    # Now add on any disconnected triangles
    encode_triangles(disconnected_triangles, fmt_str, triangle_strips)
    return triangle_strips


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
    polygon.vertex_count = len(vertex)
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
    face_point_len = len(face_indices)
    polygon.face_count = face_point_len
    data = get_triangle_strips(face_indices, fmt_str)
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
    encode_vertex_data(vert, vertices)
    mdl0.add_to_group(mdl0.vertices, vert)
    index_groups = [vertices.face_indices]
    if normals:
        normal = Normal(name, mdl0)
        encode_normal_data(normal, normals)
        mdl0.add_to_group(mdl0.normals, normal)
        index_groups.append(normals.face_indices)
    else:
        normal = None
    if colors:
        color = Color(name, mdl0)
        color.encode_data(colors)
        mdl0.add_to_group(mdl0.colors, color)
        index_groups.append(colors.face_indices)
    else:
        color = None
    uvs = []
    uv_i = len(mdl0.texCoords)
    for x in tex_coord_groups:
        tex = TexCoord('#{}'.format(uv_i), mdl0)
        encode_uv_data(tex, x)
        tex.index = uv_i
        mdl0.texCoords.append(tex)
        uv_i += 1
        uvs.append(tex)
        index_groups.append(x.face_indices)
    p = Polygon(name, mdl0)
    encode_polygon_data(p, vert, normal, color, uvs, np.stack(index_groups, axis=-1))
    mdl0.add_to_group(mdl0.objects, p)
    return p


class PointCollection:

    def __init__(self, points, face_indices, minimum=None, maximum=None):
        """
        :param points: multi-dimensional list/array of points
        :param face_indices: ndarray of triangle indices, indexing points
        :param minimum: the minimum value
        :param maximum: the maximum value
        """
        self.points = points
        self.face_indices = face_indices
        width = len(points[0])
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

    def consolidate_points(self):
        points = self.points
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
        if len(new_points) >= point_len - 5:  # Not much gain
            return points
        self.points = np.array(new_points, points.dtype)
        # Next, update the face indices
        face_indices = self.face_indices
        face_height = len(face_indices)
        face_width = len(face_indices[0])
        for i in range(face_height):
            x = face_indices[i]
            for j in range(face_width):
                x[j] = index_remapper[x[j]]
        return self.points

    def encode_points(self, multiplier, dtype):
        x = np.around(self.points * multiplier)
        self.points = x.astype(dtype)
