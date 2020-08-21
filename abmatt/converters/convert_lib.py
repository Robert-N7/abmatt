from struct import pack

import numpy as np

from brres.mdl0.color import Color
from brres.mdl0.normal import Normal
from brres.mdl0.polygon import Polygon
from brres.mdl0.texcoord import TexCoord
from brres.mdl0.vertex import Vertex


def encode_polygon_data(polygon, vertex, normal, color, uvs, face_indices):
    # set up vertex declaration
    polygon.vertex_format = vertex.format
    polygon.vertex_divisor = vertex.divisor
    if len(vertex) > 0xff:
        polygon.vertex_index_format = polygon.INDEX_FORMAT_SHORT
        fmt_str = 'H'
    else:
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
            fmt_str += 'B'
    else:
        polygon.normal_index_format = polygon.INDEX_FORMAT_NONE
    if color:
        if len(color) > 0xff:
            polygon.color0_index_format = polygon.INDEX_FORMAT_SHORT
            fmt_str += 'H'
        else:
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
    face_point_len = len(face_indices[0])
    polygon.face_count = face_point_len / 3
    data = bytearray(pack('>BH', 0x90, face_point_len))
    for i in range(face_point_len):
        data.extend(pack(fmt_str, [x[i] for x in face_indices]))
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
    vert.encode_data(vertices)
    mdl0.add_to_group(mdl0.vertices, vert)
    index_groups = vertices.face_indicies
    if mdl0.normals:
        normal = Normal(name, mdl0)
        normal.encode_data(normals)
        mdl0.add_to_group(mdl0.normals, normal)
        np.append(index_groups, normals.face_indicies, axis=1)
    else:
        normal = None
    if colors:
        color = Color(name, mdl0)
        color.encode_data(colors)
        mdl0.add_to_group(mdl0.colors, color)
        np.append(index_groups, colors.face_indicies, axis=1)
    else:
        color = mdl0.get_default_color()
    uvs = []
    uv_i = len(mdl0.texCoords)
    for x in tex_coord_groups:
        tex = TexCoord('#{}'.format(uv_i), mdl0)
        tex.index = uv_i
        mdl0.texCoords.append(tex)
        uv_i += 1
        uvs.append(tex)
        np.append(index_groups, x.face_indicies, axis=1)
    p = Polygon(name, mdl0)
    encode_polygon_data(p, vert, normal, color, uvs, index_groups)
    mdl0.add_to_group(mdl0.objects, p)
    return p
