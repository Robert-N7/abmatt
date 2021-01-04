"""Objects (Polygons)"""

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.node import Node, get_item_by_index, Clipable

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

    def paste(self, item):
        raise NotImplementedError()


    def __init__(self, name, parent, binfile=None):
        self.tex_divisor = [0] * 8
        self.tex_e = [1] * 8
        self.material = None
        self.priority = 0
        self.tri_groups = None
        self.visible_bone = None
        super(Polygon, self).__init__(name, parent, binfile)

    def begin(self):
        self.vertex_index = -1
        self.normal_index = -1
        self.color0_index = -1
        self.color1_index = -1
        self.uv_indices = [-1] * 8
        self.weight_index = -1
        self.uv_mtx_indices = [-1] * 8
        self.vertices = None
        self.facepoint_count = 0
        self.face_count = 0
        self.colors = [None, None]
        self.color_count = 0
        self.normals = None
        self.encode_str = '>'
        self.uvs = [None] * 8
        self.uv_count = 0
        self.data = None
        self.flags = 0
        self.bone = None
        self.visible_bone = self.parent.bones[0]
        self.bone_table = None
        self.fur_vector = None
        self.fur_coord = None
        self.vertex_e = 1
        self.normal_index3 = self.normal_e = 0
        self.color0_e = self.color1_e = 1

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
                AutoFix.get().error(f'Polygon {self.name} in {self.parent.parent.name} tri index {index} out of range.')


    def add_bone_table(self, table):
        self.bone_table = table
        self.bone = None

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

    def get_bone(self):
        return self.visible_bone

    def check(self, verts, norms, uvs, colors, materials):  # as we go along, gather verts norms uvs colors materials
        modified = False
        vertices = self.get_vertex_group()
        if vertices:
            verts.add(vertices.name)
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
                AutoFix.get().info(f'{self.name} has unused vertex colors', 4)
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
                    AutoFix.get().info(f'{self.name} UV Channel {i} is not used by material.', 3)
            else:
                break
        if uvs_used:
            AutoFix.get().warn(f'{self.name} does not have UV channel(s) {uvs_used} but the material uses them!')
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

    def has_weighted_matrix(self):
        return self.weight_index >= 0

    def has_uv_matrix(self, i):
        return self.uv_mtx_indices[i] >= 0

    def has_normals(self):
        return self.normals is not None
