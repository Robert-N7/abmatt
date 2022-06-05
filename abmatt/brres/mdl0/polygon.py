"""Objects (Polygons)"""
from copy import deepcopy

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib import decoder
from abmatt.brres.lib.node import Clipable

INDEX_FORMAT_NONE = 0
INDEX_FORMAT_DIRECT = 1
INDEX_FORMAT_BYTE = 2
INDEX_FORMAT_SHORT = 3


class Polygon(Clipable):
    @property
    def SETTINGS(self):
        raise NotImplementedError()

    def set_str(self, key, value):
        raise NotImplementedError()

    def get_str(self, key):
        raise NotImplementedError()

    def paste(self, other):
        parent = self.parent
        parent_diff = self.parent is not other.parent
        self.tex_e = other.tex_e
        self.decoded = None
        self.priority = other.priority
        self.vertex_index = other.vertex_index
        self.normal_index = other.normal_index
        self.color0_index = other.color0_index
        self.color1_index = other.color1_index
        self.uv_indices = deepcopy(other.uv_indices)
        self.weight_index = other.weight_index
        self.uv_mtx_indices = deepcopy(other.uv_mtx_indices)
        self.vertices = deepcopy(other.vertices)
        self.facepoint_count = other.facepoint_count
        self.face_count = other.face_count
        self.colors = deepcopy(other.colors)
        self.color_count = other.color_count
        self.normals = deepcopy(other.normals)
        self.encode_str = other.encode_str
        self.uvs = deepcopy(other.uvs)
        self.uv_count = other.uv_count
        self.data = deepcopy(other.data)
        self.flags = deepcopy(other.flags)
        self.bone_table = deepcopy(other.bone_table)
        self.vertex_e = other.vertex_e
        self.normal_index3 = other.normal_index3
        self.color0_e = other.color0_e
        if parent:
            parent.vertices.append(self.vertices)
            parent.colors.extend([x for x in self.colors if x])
            parent.uvs.extend([x for x in self.uvs if x])
            parent.normals.append(self.normals)
        if parent_diff:
            self.visible_bone = deepcopy(other.visible_bone)
            self.linked_bone = deepcopy(other.linked_bone)
            if parent:
                parent.add_bone(self.visible_bone)
                if self.visible_bone is not self.linked_bone:
                    parent.add_bone(self.linked_bone)
                parent.update_polygon_material(self, self.material, other.material)
        else:   # parent is same
            self.visible_bone = other.visible_bone
            self.linked_bone = other.linked_bone

    def __deepcopy__(self, memodict={}):
        p = Polygon(self.name, None)
        p.paste(self)
        return p

    def __init__(self, name, parent, binfile=None):
        self.tex_e = [1] * 8
        self.material = None
        self.decoded = None
        self.priority = 0
        self.visible_bone = None
        super(Polygon, self).__init__(name, parent, binfile)

    def __eq__(self, other):
        return super().__eq__(other) and self.encode_str == other.encode_str and self.face_count == other.face_count \
               and self.weight_index == other.weight_index and self.vertex_index == other.vertex_index \
               and self.normal_index == other.normal_index and self.color0_index == other.color0_index \
               and self.uv_indices == other.uv_indices and self.uv_mtx_indices == other.uv_mtx_indices \
               and self.facepoint_count == other.facepoint_count and self.vertices == other.vertices \
               and self.colors == other.colors and self.normals == other.normals and self.uvs == other.uvs \
               and self.flags == other.flags and self.linked_bone == other.linked_bone \
               and self.visible_bone == other.visible_bone and self.flags == other.flags \
               and self.vertex_e == other.vertex_e and self.normal_index3 == other.normal_index3 \
               and self.color0_e == other.color0_e and self.normal_e == other.normal_e \
               and self.priority == other.priority and self.material == other.material and self.data == other.data

    def __hash__(self):
        return super().__hash__()

    def __reset(self):
        # The face point indices, also indexes into the encode string
        self.vertex_index = -1
        self.normal_index = -1
        self.color0_index = -1
        self.color1_index = -1
        self.uv_indices = [-1] * 8
        self.weight_index = -1
        self.uv_mtx_indices = [-1] * 8
        self.vertices = None
        self.linked_bone = None
        self.decoded = None
        self.facepoint_count = 0
        self.face_count = 0
        self.colors = [None, None]
        self.color_count = 0
        self.normals = None
        self.encode_str = '>'
        self.uvs = [None] * 8
        self.uv_count = 0
        self.data = None

    def begin(self):
        self.__reset()
        self.flags = 0
        self.visible_bone = self.parent.bones[0] if self.parent else None
        self.bone_table = None
        self.fur_vector = None
        self.fur_coord = None
        self.vertex_e = 1
        self.normal_index3 = self.normal_e = 0
        self.color0_e = self.color1_e = 1

    def get_decoded(self):
        if self.decoded is None:
            self.decoded = decoder.decode_polygon(self)
        return self.decoded

    # These indices correspond to the triangle column index, not the group index!
    def get_weight_index(self):
        return self.weight_index

    def get_uv_matrix_index(self, uv_set_i):
        return self.uv_mtx_indices[uv_set_i]

    def get_vertex_index(self):
        return self.vertex_index

    def get_normal_index(self):
        return self.normal_index

    def get_color0_index(self):
        return self.color0_index

    def get_color1_index(self):
        return self.color1_index

    def get_uv_index(self, uv_set_i):
        return self.uv_indices[uv_set_i]

    def get_index_type(self, index):
        """
        Returns the INDEX_FORMAT
        """
        if index < 0:
            return INDEX_FORMAT_NONE
        else:
            try:
                return INDEX_FORMAT_BYTE if self.encode_str[index + 1] == 'B' else INDEX_FORMAT_SHORT
            except IndexError:
                AutoFix.error(f'Polygon {self.name} in {self.parent.parent.name} tri index {index} out of range.')

    def add_bone_table(self, table):
        self.bone_table = table
        self.linked_bone = None

    def get_vertex_group(self):
        return self.vertices

    def get_normal_group(self):
        return self.normals

    def get_uv_group(self, i=0):
        return self.uvs[i]

    def get_uvs(self):
        return self.uvs

    def count_uvs(self):
        return self.uv_count

    def get_color_group(self, i=0):
        return self.colors[i]

    def count_colors(self):
        return self.color_count

    def get_fur_vector(self):
        return self.fur_vector

    def get_fur_coord(self):
        return self.fur_coord

    def set_draw_priority(self, priority):
        if self.priority != priority:
            self.priority = priority
            self.mark_modified()
            return True
        return False

    def get_draw_priority(self):
        return self.priority

    def get_material(self):
        return self.material

    def set_material(self, material):
        my_material = self.get_material()
        if material != my_material:
            my_material = self.parent.update_polygon_material(self, my_material, material)
            self.mark_modified()
        return my_material

    def get_linked_bone(self):
        return self.linked_bone

    def check(self, verts, norms, uvs, colors, materials):  # as we go along, gather verts norms uvs colors materials
        modified = False
        vertices = self.get_vertex_group()
        if vertices:
            verts.add(vertices.name)
            if self.linked_bone:
                vertices.check_vertices(self.linked_bone)
        else:
            AutoFix.warn(f'{self.name} has no vertices!')
        normals = self.get_normal_group()
        if normals:
            norms.add(normals.name)
        material = self.get_material()
        if material:
            materials.add(material.name)
        # Colors
        my_colors = self.get_color_group()
        uses_vertex_colors = material.is_vertex_color_enabled()
        if my_colors:
            colors.add(my_colors.name)
            if not uses_vertex_colors:
                AutoFix.info(f'{self.name} has unused vertex colors', 4)
        elif uses_vertex_colors:
            b = Bug(2, 2, f'{material.name} uses vertex colors but {self.name} has no colors!',
                    'Disable vertex colors')
            material.enable_vertex_color(False)
            b.resolve()
            modified = True

        # UVs
        uvs_used = material.get_uv_channels()
        uv_count = 0
        for i in range(8):
            tex = self.get_uv_group(i)
            if tex:
                uv_count += 1
                uvs.add(tex.name)
                if i in uvs_used:
                    uvs_used.remove(i)
                else:
                    AutoFix.info(f'{self.name} UV Channel {i} is not used by material.', 3)
            else:
                break
        if uvs_used:
            AutoFix.warn(f'{self.name} does not have UV channel(s) {uvs_used} but the material uses them!')
        self.uv_count = uv_count
        return modified

    def get_bone_table(self):
        return self.bone_table

    def has_vertices(self):
        return self.vertices is not None

    def has_color0(self):
        return self.colors[0] is not None

    def has_color1(self):
        return self.colors[1] is not None

    def has_uv_group(self, i):
        return self.uvs[i] is not None

    def has_weights(self):
        return self.weight_index >= 0

    def has_uv_matrix(self, i):
        return self.uv_mtx_indices[i] >= 0

    def has_normals(self):
        return self.normals is not None

    def before_recode(self):
        """Should only be called if recoding"""
        self.parent.remove_vertices(self)
        self.parent.remove_normals(self)
        self.parent.remove_colors(self)
        self.parent.remove_uvs(self)
        self.__reset()
