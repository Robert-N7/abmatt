from copy import deepcopy
from struct import pack

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres.mdl0.color import Color
from abmatt.brres.mdl0.normal import Normal
from abmatt.brres.mdl0.polygon import Polygon
from abmatt.brres.mdl0.texcoord import TexCoord
from abmatt.brres.mdl0.vertex import Vertex
from abmatt.converters.error import ConvertError
from abmatt.converters.triangle import TriangleSet, encode_triangles, encode_triangle_strip, get_weighted_tri_groups


class Geometry:
    ENABLE_VERTEX_COLORS = True

    def __init__(self, name, material_name, vertices, texcoords=None, normals=None, colors=None, triangles=None,
                 influences=None, linked_bone=None):
        self.name = name
        self.index = 0
        self.encoder = None
        self.encoded = None
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
        self.has_uv_mtx = None
        self.priority = 0

    def __deepcopy__(self, memodict={}):
        new = Geometry(self.name, self.material_name, deepcopy(self.vertices), deepcopy(self.texcoords),
                       deepcopy(self.normals), deepcopy(self.colors), deepcopy(self.triangles),
                       deepcopy(self.influences), self.linked_bone)
        new.has_uv_mtx = self.has_uv_mtx
        new.priority = self.priority
        return new

    def __eq__(self, other):
        return other is not None and type(other) == Geometry and self.name == other.name and \
               self.vertices == other.vertices and self.texcoords == other.texcoords and self.colors == other.colors \
               and self.normals == other.normals and self.material_name == other.material_name and \
               self.influences == other.influences and self.triangles == other.triangles and \
               self.linked_bone == other.linked_bone

    def combine(self, geometry):
        """Combines geometries if they match up
        influences are not combined so they must be equal
        """
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
            self.colors.combine(geometry.colors, True)
        if self.triangles is not None and geometry.triangles is not None:
            self.triangles = np.append(self.triangles, geometry.triangles, 0)
        return True

    def swap_y_z_axis(self):
        points = self.vertices.points
        points[:, [1, 2]] = points[:, [2, 1]]
        points[:, 2] *= -1
        if self.normals:
            points = self.normals.points
            points[:, [1, 2]] = points[:, [2, 1]]

    def apply_linked_bone_bindings(self):
        self.influences.apply_world_position(np.array(self.vertices))

    def apply_matrix(self, matrix):
        if matrix is not None:
            self.vertices.apply_affine_matrix(matrix)

    def get_linked_bone(self):
        if not self.linked_bone and self.influences and not self.influences.is_mixed():
            self.linked_bone = self.influences.get_single_bone_bind()
        return self.linked_bone

    def ipp(self):
        j = self.index
        self.index += 1
        return j

    def recode(self, original):
        original.before_recode()
        p = self.__encode(original)
        p.after_recode()
        return p

    def __encode(self, polygon):
        mdl = polygon.parent
        self.fmt_str = '>'
        if self.__encode_influences(polygon, self.influences, polygon.visible_bone):
            polygon.weight_index = self.ipp()
        self.__encode_tex_matrices(polygon, self.has_uv_mtx)
        if self.__encode_vertices(polygon, self.vertices, mdl):
            polygon.vertex_index = self.ipp()
        if self.__encode_normals(polygon, self.normals, mdl):
            polygon.normal_index = self.ipp()
        if self.__encode_colors(polygon, self.colors, mdl, False):
            polygon.color0_index = self.ipp()
        self.__encode_texcoords(polygon, self.texcoords, mdl)
        tris = self.__construct_tris(polygon, polygon.has_weights())
        data, polygon.face_count, polygon.facepoint_count = self.__encode_tris(tris, polygon.has_weights())
        past_align = len(data) % 0x20
        if past_align:
            data.extend(b'\0' * (0x20 - past_align))

        if polygon.face_count <= 0:
            # todo, cleanup?
            return None
        polygon.data = data
        polygon.encode_str = self.fmt_str
        material = mdl.get_material_by_name(self.material_name)
        if self.colors and self.ENABLE_VERTEX_COLORS:
            if material.enable_vertex_color():
                AutoFix.info('{} has colors, enabled vertex color in light channel.'.format(self.name))
        self.encoded = polygon
        return polygon

    def encode(self, mdl, visible_bone=None, encoder=None,
               use_default_colors_if_none_found=True,
               priority=None, has_uv_mtx=None):
        if priority is not None:
            self.priority = priority
        if has_uv_mtx is not None:
            self.has_uv_mtx = has_uv_mtx
        if not visible_bone:
            if not mdl.bones:
                mdl.add_bone(mdl.name)
            visible_bone = mdl.bones[0]
        visible_bone.has_geometry = True
        self.encoded = p = Polygon(self.name, mdl)
        if encoder is not None:
            self.encoder = encoder
            encoder.before_encode(self)
        self.__encode(p)
        mdl.objects.append(p)
        material = mdl.get_material_by_name(self.material_name)
        mdl.add_definition(material, p, visible_bone, self.priority)
        if encoder:
            encoder.after_encode(p)
        return p

    def __encode_tex_matrices(self, poly, has_uv_mtx):
        if has_uv_mtx:
            for i in range(8):
                if has_uv_mtx[i]:
                    poly.uv_mtx_indices[i] = self.ipp()
                    self.fmt_str += 'B'

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

    def __remap_inf_group(self, group, tris, matrices):
        remapper = {}
        uv_mtx_count = sum(self.has_uv_mtx) if self.has_uv_mtx is not None else 0
        matrices = list(matrices)
        for i in range(len(matrices)):
            remapper[matrices[i]] = i * 3
        n_group = []
        for strip in group:
            arr = np.array(strip)
            for item in arr:
                if uv_mtx_count:
                    item[1:1+uv_mtx_count] = (item[0] + 10) * 3
                item[0] = remapper[item[0]]
            n_group.append(arr)
        n_tris = []
        for tri in tris:
            arr = np.array(tri.vertices)
            for item in arr:
                if uv_mtx_count:
                    item[1:1 + uv_mtx_count] = (item[0] + 10) * 3
                item[0] = remapper[item[0]]
            n_tris.append(arr)
        return n_group, n_tris

    def __encode_weighted_tris(self, tri_strips, tris):
        group_tristrips, group_tris, group_matrices = get_weighted_tri_groups(tri_strips, tris)
        data = bytearray()
        for i in range(len(group_tristrips)):
            matrices = group_matrices[i]
            tristrips, tris = self.__remap_inf_group(group_tristrips[i], group_tris[i], matrices)

            # now get the matrices and face points, encode them for each group
            data.extend(self.__encode_load_matrices(matrices))
            for j in range(len(tristrips)):
                encode_triangle_strip(tristrips[j], self.fmt_str, data)
            if tris:
                encode_triangles(tris, self.fmt_str, data)
        return data

    def __encode_tris(self, tris, is_weighted=False):
        tris[:, [0, 1]] = tris[:, [1, 0]]
        triset = TriangleSet(tris, is_weighted)
        if not triset:
            return None, 0, 0
        fmt_str = self.fmt_str if not is_weighted else None
        tristrips, face_count, facepoint_count, tris = triset.get_tri_strips(fmt_str)
        if is_weighted:
            tristrips = self.__encode_weighted_tris(tristrips, tris)
        return tristrips, face_count, facepoint_count

    def __encode_influences(self, polygon, influences, default_bone):
        if influences is not None and influences.is_mixed():
            polygon.weight_index = 0
            self.fmt_str += 'B'
            return True
        else:
            bone = self.get_linked_bone()
            polygon.linked_bone = self.linked_bone = bone if bone else default_bone
        return False

    def __encode_vertices(self, polygon, vertices, mdl0):
        vert = Vertex(self.name, mdl0)
        mdl0.vertices.append(vert)
        points = vertices.points
        encoder = self.encoder.vertex_encoder if self.encoder is not None else None
        if polygon.has_weights():
            for i in range(len(vertices)):
                influence = self.influences[i]
                points[i] = influence.apply_to(points[i], decode=False)
            vertex_format, vertex_divisor, remapper = vertices.encode_data(vert, True, encoder, self.influences)
            if remapper is not None:
                new_inf_map = {}
                old_inf_map = self.influences.influences
                for i in old_inf_map:
                    new_inf_map[remapper[i]] = old_inf_map[i]
                self.influences.influences = new_inf_map
        else:
            linked_bone = self.get_linked_bone()
            if linked_bone is not None:
                vertices.apply_affine_matrix(np.array(linked_bone.get_inv_transform_matrix()))
            vertices.encode_data(vert, False, encoder)
        polygon.vertices = vert
        self.fmt_str += get_index_format(vert)
        return True

    def __encode_normals(self, polygon, normals, mdl0):
        if normals:
            encoder = self.encoder.normal_encoder if self.encoder else None
            normal = Normal(self.name, mdl0)
            normal_format = normals.encode_data(normal, encoder=encoder)[0]
            mdl0.normals.append(normal)
            polygon.normal_type = normal.comp_count
            polygon.normals = normal
            self.fmt_str += get_index_format(normal)
            return True

    def __encode_colors(self, polygon, colors, mdl0, use_default):
        if colors:
            encoder = self.encoder.color_encoder if self.encoder else None
            color = colors.get_encoded_color()
            if color is None:
                color = Color(self.name, mdl0)
                mdl0.colors.append(color)
                colors.encode_data(color, encoder=encoder)
            self.fmt_str += get_index_format(color)
            polygon.colors[0] = color
            polygon.color_count = 1
            return True

    def __encode_texcoords(self, polygon, texcoords, mdl0):
        if texcoords:
            uv_encoders = self.encoder.uv_encoders if self.encoder is not None else None
            uv_i = len(mdl0.uvs)
            polygon.uv_count = len(texcoords)
            tri_indexer = len(self.fmt_str) - 1
            for i in range(polygon.uv_count):
                try:
                    encoder = uv_encoders[i] if uv_encoders else None
                except IndexError:
                    encoder = None
                x = texcoords[i]
                tex = TexCoord(self.name + '#{}'.format(i), mdl0)
                # convert xy to st
                x.flip_points()
                x.encode_data(tex, encoder=encoder)
                tex.index = uv_i + i
                mdl0.uvs.append(tex)
                self.fmt_str += get_index_format(tex)
                polygon.uv_indices[i] = tri_indexer + i
                polygon.uvs[i] = tex
            return True

    def __construct_tris(self, polygon, weighted=False):
        tris = []
        if weighted:    # build the influence indices
            remapper = self.influences.influences
            pos_indices = np.array([[remapper[y].influence_id for y in tri] for tri in self.vertices.face_indices])
            polygon.bone_table = [i for i in range(np.max(pos_indices) + 1)]
            tris.append(pos_indices)
            if self.has_uv_mtx is not None:
                for x in self.has_uv_mtx:
                    if x:
                        tris.append(pos_indices)    # this just serves as a placeholder
        tris.append(self.vertices.face_indices)
        if self.normals:
            tris.append(self.normals.face_indices)
        if self.colors:
            tris.append(self.colors.get_face_indices())
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
        raise ConvertError(f'{item.name} exceeds max length! ({len(item)})')
    elif l > 0xff:
        return 'H'
    else:
        return 'B'
