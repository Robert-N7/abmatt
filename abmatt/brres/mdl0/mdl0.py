""" MDL0 Models """
# ----------------- Model sub files --------------------------------------------
import math

from abmatt.brres.lib.matching import fuzzy_match, MATCHING
from abmatt.brres.lib.node import Node
from abmatt.brres.mdl0.definition import get_definition
from abmatt.brres.subfile import SubFile
from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.packing.pack_mdl0.pack_mdl0 import PackMdl0
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_mdl0 import UnpackMdl0
from abmatt.brres.mdl0.bone import Bone
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.pat0.pat0 import Pat0Collection
from abmatt.brres.pat0.pat0_material import Pat0MatAnimation
from abmatt.brres.srt0.srt0 import SRTCollection
from abmatt.brres.srt0.srt0_animation import SRTMatAnim


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
    VERSION_SECTIONCOUNT = {8: 11, 9:11, 10:14, 11:14}
    EXPECTED_VERSION = 11

    SETTINGS = ('name')  # todo, more settings
    DETECT_MODEL_NAME = True
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, parent, binfile=None):
        """ initialize model """
        self.srt0_collection = None
        self.pat0_collection = None
        self.DrawOpa = self.DrawXlu = self.NodeTree = self.NodeMix = None
        self.weights_by_id = None
        self.definitions = []
        self.bones = []
        self.vertices = []
        self.normals = []
        self.colors = []
        self.uvs = []
        # self.furVectors = []
        # self.furLayers = []
        self.materials = []
        # self.shaders = ShaderList()
        self.objects = []
        # self.paletteLinks = []
        # self.textureLinks = []
        self.version = 11
        self.find_min_max = False
        self.is_map_model = True if 'map' in name else False
        super(Mdl0, self).__init__(name, parent, binfile)

    def begin(self):
        self.boneTable = []
        self.boneMatrixCount = 0
        self.faceCount = 0
        self.facepoint_count = 0
        self.scaling_rule = 0
        self.texture_matrix_mode = 0
        self.parent.has_new_model = True
        for definition in ('DrawOpa', 'DrawXlu', 'NodeTree', 'NodeMix'):
            self.__setattr__(definition, get_definition(definition, self))

    def mark_unmodified(self):
        self.is_modified = False
        self._mark_unmodified_group(self.materials)

    def get_weights_by_ids(self, indices):
        weights_by_id = self.weights_by_id
        if weights_by_id is None:
            self.weights_by_id = weights_by_id = {}
            if self.NodeMix is not None:
                for x in self.NodeMix.fixed_weights:
                    self.weights_by_id[x.weight_id] = x
                for x in self.NodeMix.mixed_weights:
                    self.weights_by_id[x.weight_id] = x
        weights = []
        bonetable = self.boneTable
        for index in indices:
            # weight = bonetable[index]
            if False:
                weights.append([(weight, 1)])
            else:
                weights.append([(bonetable[x[0]], x[1]) for x in weights_by_id[index].to_inf()])
        return weights

    def set_bonetable(self, bonetable):
        self.boneTable = bonetable

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
        self.find_min_max = False

    def rebuild_header(self):
        """After encoding data, calculates the header data"""
        self.boneMatrixCount = len(self.boneTable)
        self.search_for_min_and_max()
        self.facepoint_count = sum(obj.facepoint_count for obj in self.objects)
        self.faceCount = sum(obj.face_count for obj in self.objects)


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

    @staticmethod
    def add_to_group(group, item):
        i = len(group)
        item.index = i
        group.append(item)

    # @staticmethod
    # def remove_from_group(group, item):
    #     group.remove(item)
    #     for i in range(len(group)):
    #         group[i].index = i

    def update_polygon_material(self, polygon, old_mat, new_mat):
        # polys = self.get_polys_using_material(old_mat)
        if new_mat.parent != self:  # is it a material not in the model already?
            test = self.get_material_by_name(new_mat.name)
            if test == new_mat:     # already have this material?
                new_mat = test
            else:
                m = Material.get_unique_material(new_mat.name, self)
                self.add_material(m)
                m.paste(new_mat)
                new_mat = m
        old_mat.polygons.remove(polygon)
        new_mat.polygons.append(polygon)
        polygon.material = new_mat
        if not len(old_mat.polygons):
            self.materials.remove(old_mat)
        return new_mat

    def add_material(self, material):
        self.add_to_group(self.materials, material)
        # for x in material.layers:
        #     self.add_texture_link(x.name)
        return material

    def remove_material(self, material):
        polys = self.get_polys_using_material(material)
        if polys:
            AutoFix.error('Unable to remove linked material, used by {}'.format(polys))
            return False
        self.materials.remove(material)
        return True

    def get_polys_using_material(self, material):
        return [x for x in self.objects if x.get_material() == material]

    def add_bone(self, name, parent_bone=None, has_geometry=False,
                 scale_equal=True, fixed_scale=True,
                 fixed_rotation=True, fixed_translation=True):
        b = Bone(name, self, has_geometry=has_geometry,
                 scale_equal=scale_equal, fixed_scale=fixed_scale,
                 fixed_rotation=fixed_rotation, fixed_translation=fixed_translation)
        self.add_to_group(self.bones, b)
        b.weight_id = len(self.boneTable)
        self.boneTable.append(self.boneMatrixCount)
        if parent_bone:
            parent_index = parent_bone.index    # todo check this
            parent_bone.link_child(b)
        else:
            parent_index = 0
        self.NodeTree.add_entry(self.boneMatrixCount, parent_index)
        self.boneMatrixCount += 1
        return b

    def add_definition(self, material, polygon, bone=None, priority=0):
        material.polygons.append(polygon)
        polygon.material = material
        polygon.visible_bone = bone
        polygon.draw_priority = priority
        # if bone is None:
        #     bone = self.bones[0]
        # definitions = self.DrawOpa if not material.xlu else self.DrawXlu
        # definitions.add_entry(material.index, polygon.index, bone.index, priority)

    # ---------------------------------- SRT0 ------------------------------------------
    def set_srt0(self, srt0_collection):
        self.srt0_collection = srt0_collection
        not_found = []
        for x in srt0_collection:
            mat = self.get_material_by_name(x.name)
            if not mat:
                not_found.append(x)
            else:
                mat.set_srt0(x)
        for x in not_found:
            mat = fuzzy_match(x.name, self.materials)
            desc = 'No material matching SRT0 {}'.format(x.name)
            b = Bug(1, 1, desc, 'Rename material')
            if self.RENAME_UNKNOWN_REFS and mat and not mat.srt0:
                if mat.set_srt0(x):
                    x.rename(mat.name)
                    b.resolve()
                    self.mark_modified()
            else:
                b.fix_des = 'Remove SRT0'
                if self.REMOVE_UNKNOWN_REFS:
                    srt0_collection.remove(x)
                    b.resolve()

    def add_srt0(self, material):
        anim = SRTMatAnim(material.name)
        if not self.srt0_collection:
            self.srt0_collection = self.parent.add_srt_collection(SRTCollection(self.name, self.parent))
        self.srt0_collection.add(anim)
        return anim

    def remove_srt0(self, animation):
        return self.srt0_collection.remove(animation)

    # ------------------ Pat0 --------------------------------------
    def set_pat0(self, pat0_collection):
        self.pat0_collection = pat0_collection
        not_found = []
        for x in pat0_collection:
            mat = self.get_material_by_name(x.name)
            if not mat:
                not_found.append(x)
            else:
                mat.set_pat0(x)
        for x in not_found:
            desc = 'No material matching PAT0 {}'.format(x.name)
            mat = fuzzy_match(x.name, self.materials)
            b = Bug(1, 1, desc, None)
            if self.RENAME_UNKNOWN_REFS and mat and not mat.pat0:
                b.fix_des = 'Rename to {}'.format(mat.name)
                if mat.set_pat0(x):
                    x.rename(mat.name)
                    b.resolve()
            else:
                if self.REMOVE_UNKNOWN_REFS:
                    b.fix_des = 'remove pat0'
                    pat0_collection.remove(x)
                    b.resolve()

    def add_pat0(self, material):
        if not self.pat0_collection:
            self.pat0_collection = self.parent.add_pat0_collection(Pat0Collection(self.name, self.parent))
        anim = Pat0MatAnimation(material.name, self.parent)
        self.pat0_collection.add(anim)
        return anim

    def remove_pat0(self, animation):
        return self.pat0_collection.remove(animation)

    # ------------------ Name --------------------------------------
    def rename(self, name):
        result = None
        if name != self.name:
            result = self.parent.renameModel(self.name, name)
            if result:
                self.name = result
                self.is_map_model = True if 'map' in name else False
            self.mark_modified()
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

    # ------------------------------- Shaders -------------------------------------------
    def getShaders(self, material_list, for_modification=True):
        return self.shaders.getShaders(material_list, for_modification)

    # ----------------------------- Tex Links -------------------------------------
    # def get_texture_link(self, name):
    #     for x in self.textureLinks:
    #         if x.name == name:
    #             return x

    def add_texture_link(self, name):
        if name != 'Null' and not self.parent.getTexture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AutoFix.get().info(notify, 4)

    def rename_texture_link(self, layer, name):
        """Attempts to rename a layer, raises value error if the texture can't be found"""
        # No link found, try to find texture matching and create link
        if name != 'Null' and not self.parent.getTexture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AutoFix.get().info(notify, 4)
        return name

    def get_trace(self):
        return self.parent.get_trace() + "->" + self.name

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>' + self.name if indentation_level else self.parent.name + "->" + self.name
        print("{}:\t{} material(s)".format(trace, len(self.materials)))
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
        copy = super().__deepcopy__(memodict)
        sections = [copy.definitions, copy.bones, copy.vertices, copy.normals,
                    copy.colors, copy.uvs,
                    # copy.furVectors, copy.furLayers,
                    copy.materials, copy.shaders, copy.objects,
                    ]
        for x in sections:
            for y in x:
                y.link_parent(copy)
        shaders = copy.shaders
        srt0_group = self.srt0_collection
        pat0_group = self.pat0_collection
        for x in copy.materials:
            shader = shaders[x.name]
            x.shader = shader
            shader.material_name = x
            if srt0_group:
                srt0 = srt0_group[x.name]
                if srt0:
                    x.srt0 = srt0
            if pat0_group:
                pat0 = pat0_group[x.name]
                if pat0:
                    x.pat0 = pat0
        return copy

    def link_parent(self, parent):
        super().link_parent(parent)
        brres_textures = self.getTextureMap()
        if self.pat0_collection:
            for x in self.pat0_collection:
                x.brres_textures = brres_textures

    def rename_material(self, material, new_name):
        # first check if name is available
        for x in self.materials:
            if new_name == x.name:
                raise ValueError('The name {} is already taken!'.format(new_name))
        if material.srt0:
            material.srt0.rename(new_name)
        elif self.srt0_collection:
            anim = self.srt0_collection[new_name]
            if anim:
                material.set_srt0(anim)
        if material.pat0:
            material.pat0.rename(new_name)
        elif self.pat0_collection:
            anim = self.pat0_collection[new_name]
            if anim:
                material.set_pat0(anim)
        return new_name

    def getTextureMap(self):
        return self.parent.get_texture_map()

    # --------------------------------------- Check -----------------------------------
    def check(self, expected_name=None):
        """Checks model (somewhat) for validity
            texture_map: dictionary of tex_name:texture
        """
        super(Mdl0, self).check()
        texture_map = self.getTextureMap()
        for x in self.materials:
            x.check(texture_map)
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
        uvs = set()
        normals = set()
        vertices = set()
        colors = set()
        for x in self.objects:
            if x.check(vertices, normals, uvs, colors):
                self.mark_modified()
        for x in self.uvs:
            if x.check():
                self.mark_modified()
        for x in self.vertices:
            if x.check():
                self.mark_modified()
        for x in self.normals:
            if x.check():
                self.mark_modified()

    def add_map_bones(self):
        current_names = [bone.name for bone in self.bones]
        parent = self.bones[0]
        minimum = self.minimum
        maximum = self.maximum
        if 'posLD' not in current_names:
            b = self.add_bone('posLD', parent, fixed_translation=False, has_geometry=False)
            left = round(minimum[0] - 8000)
            down = round(maximum[2] + 8000)
            b.set_translation((left, 0, down))
            self.mark_modified()
        if 'posRU' not in current_names:
            b = self.add_bone('posRU', parent, fixed_translation=False, has_geometry=False)
            right = round(maximum[0] + 8000)
            up = round(minimum[2] - 8000)
            b.set_translation((right, 0, up))
            self.mark_modified()

    def get_used_textures(self):
        textures = set()
        for x in self.materials:
            for y in x.layers:
                textures.add(y.name)
        return textures

    # ---------------START PACKING STUFF -------------------------------------
    def unpack(self, binfile):
        UnpackMdl0(self, binfile)

    def pack(self, binfile):
        PackMdl0(self, binfile)

    # -------------- END PACKING STUFF ---------------------------------------
