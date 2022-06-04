""" MDL0 Models """
# ----------------- Model sub files --------------------------------------------
import math
import string

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.decoder import decode_mdl0_influences
from abmatt.brres.lib.matching import fuzzy_match, MATCHING, it_eq
from abmatt.brres.lib.node import Node, get_name_mapping
from abmatt.brres.lib.packing.pack_mdl0.pack_mdl0 import PackMdl0
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_mdl0 import UnpackMdl0
from abmatt.brres.mdl0.bone import Bone
from abmatt.brres.mdl0.definition import get_definition
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.subfile import SubFile


class ModelGeneric(Node):
    """ A generic model class - most data structures have similar type of header"""

    def unpack(self, binfile):
        """ Unpacks some ptrs but mostly just leaves data as bytes """
        binfile.start()
        self.length, mdl = binfile.read("Ii", 8)
        offset = binfile.beginOffset + mdl
        [self.dataPtr] = binfile.read("I", 4)
        binfile.advance(4)  # ignore, we already have name
        [self.index] = binfile.read("I", 4)
        # doesn't do much unpacking
        self.data = binfile.readRemaining(self.length)
        # printCollectionHex(self.data)
        binfile.end()

    def pack(self, binfile):
        """ Packs into binfile """
        binfile.start()
        binfile.write("Ii", self.length, binfile.getOuterOffset())
        binfile.write("I", self.dataPtr)
        binfile.storeNameRef(self.name)
        binfile.write("I", self.index)
        binfile.writeRemaining(self.data)
        binfile.end()


class FurLayer(ModelGeneric):
    """ Fur Layer model data """
    pass


class FurVector(ModelGeneric):
    """ Fur Vector model data """
    pass


# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
class Mdl0(SubFile):
    """ Model Subfile """

    MAGIC = "MDL0"
    EXT = 'mdl0'
    VERSION_SECTIONCOUNT = {8: 11, 9: 11, 10: 14, 11: 14}
    EXPECTED_VERSION = 11

    SETTINGS = ('name',)
    DETECT_MODEL_NAME = True
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True
    REMOVE_UNUSED_REFS = False

    def __init__(self, name, parent, binfile=None):
        """ initialize model """
        self.DrawOpa = self.DrawXlu = self.NodeTree = self.NodeMix = None
        self.weights_by_id = None
        self.rebuild_head = False
        self.bone_matrix_count = 0
        self.minimum = [0] * 3
        self.maximum = [0] * 3
        self.definitions = []
        self.bones = []
        self.vertices = []
        self.normals = []
        self.colors = []
        self.uvs = []
        self.face_count = 0
        self.facepoint_count = 0
        self.scaling_rule = 0
        self.texture_matrix_mode = 0
        # self.furVectors = []
        # self.furLayers = []
        self.materials = []
        self.objects = []
        self.influences = None
        # self.paletteLinks = []
        # self.textureLinks = []
        self.version = 11
        self.is_map_model = True if 'map' in name else False
        super(Mdl0, self).__init__(name, parent, binfile)

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return super().__eq__(other) and self.objects == other.objects and self.DrawOpa == other.DrawOpa \
               and self.DrawXlu == other.DrawXlu and self.NodeTree == other.NodeTree and self.NodeMix == other.NodeMix \
               and it_eq(self.minimum, other.minimum) and it_eq(self.maximum, other.maximum) \
               and self.facepoint_count == other.facepoint_count and self.face_count == other.face_count \
               and self.scaling_rule == other.scaling_rule and self.texture_matrix_mode == other.texture_matrix_mode \
               and self.bone_table == other.bone_table

    def get_influences(self):
        if self.influences is None:
            self.influences = decode_mdl0_influences(self)
        return self.influences

    def begin(self):
        self.bone_table = []
        self.parent.has_new_model = True
        for definition in ('DrawOpa', 'DrawXlu', 'NodeTree', 'NodeMix'):
            self.__setattr__(definition, get_definition(definition, self))

    def mark_unmodified(self):
        self.is_modified = False
        self._mark_unmodified_group(self.materials)

    def set_bonetable(self, bonetable):
        self.bone_table = bonetable

    def search_for_min_and_max(self):
        minimum = [math.inf] * 3
        maximum = [-math.inf] * 3
        for vertex in self.vertices:
            vert_min = vertex.minimum
            vert_max = vertex.maximum
            for i in range(3):
                if vert_min[i] < minimum[i]:
                    minimum[i] = vert_min[i]
                if vert_max[i] > maximum[i]:
                    maximum[i] = vert_max[i]
        self.minimum = minimum
        self.maximum = maximum
        bone = self.bones[0]
        bone.minimum = [x for x in self.minimum]
        bone.maximum = [x for x in self.maximum]

    def rebuild_node_tree(self):
        new_tree = []
        for bone in self.bones:
            parent_index = bone.b_parent.weight_id if bone.b_parent else 0
            new_tree.append((bone.index, parent_index))
        self.NodeTree.nodes = new_tree

    def rebuild_header(self):
        """After encoding data, calculates the header data"""
        self.bone_matrix_count = len(self.bone_table)
        self.search_for_min_and_max()
        self.facepoint_count = sum(obj.facepoint_count for obj in self.objects)
        self.face_count = sum(obj.face_count for obj in self.objects)
        self.rebuild_node_tree()
        self.rebuild_head = False

    def rebuild_vertex_refs(self):
        mapper = get_name_mapping(self.vertices)
        for poly in self.objects:
            poly.vertices = mapper[poly.vertices.name]

    def rebuild_normal_refs(self):
        mapper = get_name_mapping(self.normals)
        for poly in self.objects:
            normals = poly.get_normal_group()
            if normals:
                poly.normals = mapper[normals.name]

    def rebuild_uv_refs(self):
        mapper = get_name_mapping(self.uvs)
        for poly in self.objects:
            for i in range(poly.count_uvs()):
                poly.uvs[i] = mapper[poly.get_uv_group(i).name]

    def rebuild_color_refs(self):
        mapper = get_name_mapping(self.colors)
        for poly in self.objects:
            colors = poly.get_color_group()
            if colors:
                poly.colors[0] = mapper[colors.name]

    def get_str(self, key):
        if key == 'name':
            return self.name
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def set_str(self, key, value):
        if key == 'name':
            self.rename(value)
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def update_polygon_material(self, polygon, old_mat, new_mat):
        # polys = self.get_polys_using_material(old_mat)
        if new_mat.parent is not self:  # is it a material not in the model already?
            test = self.get_material_by_name(new_mat.name)
            if new_mat.parent is not None:
                new_brres = new_mat.parent.parent
                my_brres = self.parent
                if my_brres is not None and new_brres is not None:
                    my_brres.paste_material_tex0s(new_mat, new_brres)
            if test == new_mat:  # already have this material?
                new_mat = test
            else:
                m = Material.get_unique_material(new_mat.name, self)
                self.add_material(m)
                m.paste(new_mat)
                new_mat = m
        new_mat.add_poly_ref(polygon)
        if old_mat:
            old_mat.remove_poly_ref(polygon)
        polygon.material = new_mat
        if old_mat and not len(old_mat.polygons):
            self.materials.remove(old_mat)
        # self.mark_modified()
        return new_mat

    @staticmethod
    def __remove_group_item(item, group, if_not_in_group):
        if item is not None and item in group:
            for x in if_not_in_group:
                if x is item:
                    return False
            group.remove(item)
            return True

    def remove_vertices(self, polygon):
        result = self.__remove_group_item(
            polygon.get_vertex_group(),
            self.vertices,
            [x.get_vertex_group() for x in self.objects if x is not polygon]
        )
        if result:
            self.rebuild_head = True
            self.mark_modified()
        return result

    def remove_normals(self, polygon):
        result = self.__remove_group_item(
            polygon.get_normal_group(),
            self.normals,
            [x.get_normal_group() for x in self.objects if x is not polygon]
        )
        if result:
            self.rebuild_head = True
            self.mark_modified()
        return result

    def remove_colors(self, polygon):
        result = self.__remove_group_item(
            polygon.get_color_group(),
            self.colors,
            [x.get_color_group() for x in self.objects if x is not polygon]
        )
        if result:
            self.rebuild_head = True
            self.mark_modified()
        return result

    def remove_uvs(self, polygon, uvs=None):
        if not uvs:
            uvs = [polygon.get_uv_group(i) for i in range(polygon.uv_count)]
        all_used = []
        for x in self.objects:
            if x is not polygon:
                all_used.extend([x.get_uv_group(i) for i in range(x.uv_count)])
        result = True
        for x in uvs:
            if not self.__remove_group_item(
                uvs,
                self.uvs,
                all_used
            ):
                result = False
        if result:
            self.mark_modified()
            self.rebuild_head = True
        return result

    def remove_polygon(self, polygon):
        self.objects.remove(polygon)
        self.rebuild_head = True
        if len(polygon.material.polygons) == 1:
            self.remove_material(polygon.material)
        self.remove_vertices(polygon)
        self.remove_normals(polygon)
        self.remove_colors(polygon)
        self.remove_uvs(polygon)
        self.mark_modified()

    def add_material(self, material):
        """
        Adds material to model
        Throws a runtime exception if the material is already in model or if the material is used by another model
        """
        # check material parent, but does not check for duplicates!
        if material.parent:
            if material.parent is not self:
                raise RuntimeError(f'Material {material.name} is already used by {material.parent.name}')
        else:
            material.link_parent(self)
        if self.get_material_by_name(material.name):
            raise RuntimeError(f'Material with name {material.name} is already in model!')
        self.materials.append(material)
        self.mark_modified()
        return material

    def remove_material(self, material):
        polys = self.get_polys_using_material(material)
        if polys:
            raise RuntimeError('Unable to remove linked material, used by {}'.format(polys))
        self.materials.remove(material)
        self.mark_modified()

    def get_polys_using_material(self, material):
        return [x for x in self.objects if x.get_material() == material]

    def add_bone(self, bone, parent_bone=None, has_geometry=False,
                 scale_equal=True, fixed_scale=True,
                 fixed_rotation=True, fixed_translation=True):
        if type(bone) is not Bone:
            b = Bone(bone, self, has_geometry=has_geometry,
                     scale_equal=scale_equal, fixed_scale=fixed_scale,
                     fixed_rotation=fixed_rotation, fixed_translation=fixed_translation)
        else:
            b = bone
        b.index = len(self.bones)
        self.bones.append(b)
        if self.bone_table is None:
            self.bone_table = []
        b.weight_id = len(self.bone_table)
        self.bone_table.append(self.bone_matrix_count)
        if parent_bone:
            parent_bone.link_child(b)
        self.rebuild_head = True
        self.bone_matrix_count += 1
        return b

    def add_definition(self, material, polygon, visible_bone=None, priority=0):
        material.add_poly_ref(polygon)
        polygon.material = material
        polygon.visible_bone = visible_bone
        polygon.priority = priority
        self.rebuild_head = True

    # ------------------ Name --------------------------------------
    def rename(self, name):
        for x in self.parent.models:
            if x is not self and x.name == name:
                AutoFix.error('Unable to rename {}, the model {} already exists!'.format(self.name, name))
                return False
        old_name = self.name
        result = super().rename(name)
        if result:
            self.parent.on_model_rename(old_name, name)
            self.is_map_model = True if 'map' in name else False
        return result

    # ------------------------------------ Materials ------------------------------
    def get_material_by_name(self, name):
        """Exact naming"""
        for m in self.materials:
            if m.name == name:
                return m
        return None

    def get_material_by_id(self, id):
        for x in self.materials:
            if x.index == id:
                return x

    def get_materials_by_name(self, name):
        return MATCHING.findAll(name, self.materials)

    def add_texture_link(self, name):
        if name != 'Null' and not self.parent.get_texture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AutoFix.info(notify, 4)

    def rename_texture_link(self, layer, name):
        """Attempts to rename a layer, raises value error if the texture can't be found"""
        # No link found, try to find texture matching and create link
        if name != 'Null' and not self.parent.get_texture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AutoFix.info(notify, 4)
        return name

    def get_trace(self):
        return self.parent.get_trace() + "->" + self.name

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>' + self.name if indentation_level else self.parent.name + "->" + self.name
        AutoFix.info("{}:\t{} material(s)".format(trace, len(self.materials)), 1)
        indentation_level += 1
        # pass it along
        for x in self.materials:
            x.info(key, indentation_level)

    # ---------------------------------------------- CLIPBOARD -------------------------------------------
    def clip(self, clipboard):
        clipboard[self.name] = self

    def clip_find(self, clipboard):
        return clipboard.get(self.name)

    def paste(self, item):
        self.paste_group(self.materials, item.materials)

    def __deepcopy__(self, memodict={}):
        raise NotImplementedError()  # hasn't been tested and it seems dangerous
        copy = super().__deepcopy__(memodict)
        sections = [copy.definitions, copy.bones, copy.vertices, copy.normals,
                    copy.colors, copy.uvs,
                    # copy.furVectors, copy.furLayers,
                    copy.materials, copy.objects,
                    ]
        for x in sections:
            for y in x:
                y.link_parent(copy)
        return copy

    def link_parent(self, parent):
        super().link_parent(parent)
        for x in self.materials:
            x.on_brres_link(parent)

    def on_material_rename(self, material, new_name):
        if material.srt0:
            material.srt0.rename(new_name)
        if material.pat0:
            material.pat0.rename(new_name)
        return new_name

    def getTextureMap(self):
        return self.parent.get_texture_map()

    # --------------------------------------- Check -----------------------------------
    def check_group(self, group, used_set, extras=None):
        """
        helper function for check
        :param group, the group to check
        :param used_set, set of items with references
        """
        to_remove = []
        for x in group:
            if x.name not in used_set:
                AutoFix.info('Unused reference {}'.format(x.name), 3)
                if self.REMOVE_UNUSED_REFS:
                    to_remove.append(x)
            if extras and x.check(extras):
                self.mark_modified()
            elif x.check():
                self.mark_modified()
        if to_remove:
            AutoFix.info('(FIXED) Removed unused refs')
            for x in to_remove:
                group.remove(x)

    def check(self, expected_name=None):
        """
        Checks model (somewhat) for validity
        """
        super(Mdl0, self).check()
        if self.rebuild_head:
            self.rebuild_header()
        if expected_name:
            if expected_name != self.name:
                b = Bug(2, 2, 'Model name does not match file', 'Rename to {}'.format(expected_name))
                if self.DETECT_MODEL_NAME:
                    if self.rename(expected_name):
                        b.resolve()
                        self.mark_modified()
            if self.is_map_model:
                names = [x.name for x in self.bones]
                if 'posLD' not in names or 'posRU' not in names:
                    b = Bug(2, 2, 'Missing map model bones', 'Added map bones')
                    self.add_map_bones()
                    b.resolve()
                    self.mark_modified()
        # as we go along, keep track of those references used
        uvs = set()
        normals = set()
        vertices = set()
        colors = set()
        materials = set()
        for x in self.objects:
            if x.check(vertices, normals, uvs, colors, materials):
                self.mark_modified()
        texture_map = self.getTextureMap()
        self.check_group(self.materials, materials, extras=texture_map)
        self.check_group(self.vertices, vertices)
        self.check_group(self.normals, normals)
        self.check_group(self.uvs, uvs)
        self.check_group(self.colors, colors)
        if not len(self.bones):  # no bones???
            name = expected_name if expected_name else 'default'
            AutoFix.warn('No bones in model, adding bone {}'.format(name))
            self.add_bone(name)

    def add_map_bones(self):
        current_names = [bone.name for bone in self.bones]
        parent = self.bones[0]
        minimum = self.minimum
        maximum = self.maximum
        if 'posLD' not in current_names:
            b = self.add_bone('posLD', parent, fixed_translation=False, has_geometry=False)
            left = round(minimum[0] - 6000)
            down = round(maximum[2] + 6000)
            b.set_translation((left, 0, down))
            self.mark_modified()
        if 'posRU' not in current_names:
            b = self.add_bone('posRU', parent, fixed_translation=False, has_geometry=False)
            right = round(maximum[0] + 6000)
            up = round(minimum[2] - 6000)
            b.set_translation((right, 0, up))
            self.mark_modified()

    def get_used_textures(self):
        textures = set()
        for x in self.materials:
            textures |= x.get_used_textures()
        return textures

    # ---------------START PACKING STUFF -------------------------------------
    def unpack(self, binfile):
        UnpackMdl0(self, binfile)

    def pack(self, binfile):
        PackMdl0(self, binfile)

    # -------------- END PACKING STUFF ---------------------------------------
