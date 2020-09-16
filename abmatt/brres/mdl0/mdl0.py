""" MDL0 Models """
# ----------------- Model sub files --------------------------------------------
import math

from abmatt.brres.lib.autofix import AUTO_FIXER, Bug
from abmatt.brres.lib.binfile import Folder, PackingError
from abmatt.brres.lib.matching import fuzzy_match, MATCHING
from abmatt.brres.lib.node import Node
from abmatt.brres.mdl0.bone import Bone, BoneTable
from abmatt.brres.mdl0.color import Color
from abmatt.brres.mdl0.definition import DrawList, Definition, NodeTree
from abmatt.brres.mdl0.material import Material
from abmatt.brres.mdl0.normal import Normal
from abmatt.brres.mdl0.polygon import Polygon
from abmatt.brres.mdl0.shader import Shader, ShaderList
from abmatt.brres.mdl0.texcoord import TexCoord
from abmatt.brres.mdl0.vertex import Vertex
from abmatt.brres.pat0 import Pat0MatAnimation, Pat0Collection
from abmatt.brres.srt0 import SRTMatAnim, SRTCollection
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


class TextureLink(Node):
    """ Links from textures to materials and layers """

    def __init__(self, name, parent=None, binfile=None):
        """Only tracks number of references, which serve as placeholders to be filled in by the layers"""
        super(TextureLink, self).__init__(name, parent, binfile)

    def __str__(self):
        return self.name + ' ' + str(self.num_references)

    def begin(self):
        self.num_references = 1

    def unpack(self, binfile):
        # offset = binfile.start()
        [self.num_references] = binfile.read("I", 4)
        # for i in range(self.num_references):  # ignore this?
        #     link = binfile.read("2i", 8)
        # print('{} at {}'.format(self, offset))
        # binfile.end()

    def pack(self, binfile):
        offset = binfile.start()
        # print('{} at {}'.format(self, offset))
        binfile.write("I", self.num_references)
        for i in range(self.num_references):
            binfile.mark(2)  # marks 2 references
        binfile.end()
        return offset


class FurLayer(ModelGeneric):
    """ Fur Layer model data """
    pass


class FurVector(ModelGeneric):
    """ Fur Vector model data """
    pass


# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
class Mdl0(SubFile):
    """ Model Subfile """

    MAGIC = "MDL0"
    EXT = 'mdl0'
    VERSION_SECTIONCOUNT = {8: 11, 9:11, 10:14, 11:14}
    EXPECTED_VERSION = 11
    SECTION_NAMES = ("Definitions", "Bones", "Vertices", "Normals", "Colors",
                     "UVs", "FurVectors", "FurLayers",
                     "Materials", "Shaders", "Objects", "Textures", "Palettes")

    SECTION_ORDER = (11, 0, 1, 6, 7, 8, 9, 10, 2, 3, 4, 5)

    SECTION_CLASSES = (DrawList, Bone, Vertex, Normal, Color, TexCoord, FurVector,
                       FurLayer, Material, Shader, Polygon, TextureLink, TextureLink)

    SETTINGS = ('name')  # todo, more settings
    DETECT_MODEL_NAME = True
    DRAW_PASS_AUTO = True
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, parent, binfile=None):
        """ initialize model """
        self.srt0_collection = None
        self.pat0_collection = None
        self.definitions = []
        self.bones = []
        self.vertices = []
        self.normals = []
        self.colors = []
        self.texCoords = []
        self.furVectors = []
        self.furLayers = []
        self.materials = []
        self.shaders = ShaderList()
        self.objects = []
        self.paletteLinks = []
        self.textureLinks = []
        self.version = 11
        self.sections = [self.definitions, self.bones, self.vertices, self.normals,
                         self.colors, self.texCoords, self.furVectors, self.furLayers,
                         self.materials, self.shaders, self.objects,
                         self.textureLinks, self.paletteLinks]
        super(Mdl0, self).__init__(name, parent, binfile)

    def begin(self):
        self.boneTable = BoneTable()
        self.boneCount = 0
        self.faceCount = 0
        self.facepoint_count = 0
        self.scaling_rule = 0
        self.texture_matrix_mode = 0
        self.drawOpa = DrawList(Definition.names[0], self)
        self.drawXLU = DrawList(Definition.names[1], self)
        self.nodeTree = NodeTree(Definition.names[3], self)

    def rebuild_header(self):
        """After encoding data, calculates the header data"""
        self.boneCount = len(self.bones)
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
        bone.minimum = [x for x in minimum]
        bone.maximum = [x for x in maximum]
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

    def add_material(self, material):
        self.add_to_group(self.materials, material)
        for x in material.layers:
            self.add_texture_link(x.name)
        return material

    def add_bone(self, name, parent_bone=None):
        b = Bone(name, self)
        self.add_to_group(self.bones, b)
        b.bone_id = self.boneTable.add_entry(self.boneCount)
        if parent_bone:
            parent_index = parent_bone.bone_id
            parent_bone.link_child(b)
        else:
            parent_index = 0
        self.nodeTree.add_entry(self.boneCount, parent_index)
        self.boneCount += 1
        return b

    def add_definition(self, material, polygon, bone=None, priority=0):
        if bone is None:
            bone = self.bones[0]
        definitions = self.drawOpa if not material.xlu else self.drawXLU
        definitions.add_entry(material.index, polygon.index, bone.index, priority)

    # ---------------------------------- SRT0 ------------------------------------------
    def set_srt0(self, srt0_collection):
        self.srt0_collection = srt0_collection
        not_found = []
        for x in srt0_collection:
            mat = self.getMaterialByName(x.name)
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
            mat = self.getMaterialByName(x.name)
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
        return self.parent.renameModel(self.name, name)
        # if self.srt0_collection:
        #     self.srt0_collection.rename(name)
        # if self.pat0_collection:
        #     self.pat0_collection.rename(name)
        # self.name = name

    # ------------------------------------ Materials ------------------------------
    def getMaterialByName(self, name):
        """Exact naming"""
        for m in self.materials:
            if m.name == name:
                return m
        return None

    def getMaterialByID(self, id):
        for x in self.materials:
            if x.index == id:
                return x

    def getMaterialsByName(self, name):
        return MATCHING.findAll(name, self.materials)

    def isMaterialDrawXlu(self, material_id):
        if self.drawXLU.getByMaterialID(material_id):
            return True
        return False

    def setMaterialDrawXlu(self, material_id):
        x = self.drawOpa.pop(material_id)
        if x is not None:
            self.drawXLU.insert(x)
        return x

    def setMaterialDrawOpa(self, material_id):
        x = self.drawXLU.pop(material_id)
        if x is not None:
            self.drawOpa.insert(x)
        return x

    def setDrawPriority(self, material_id, priority):
        return self.drawXLU.setPriority(material_id, priority) or self.drawOpa.setPriority(material_id, priority)

    def getDrawPriority(self, material_id):
        return self.get_definition_by_material_id(material_id).getPriority()

    def get_definition_by_material_id(self, material_id):
        definition = self.drawOpa.getByMaterialID(material_id)
        if not definition:
            definition = self.drawXLU.getByMaterialID(material_id)
        return definition

    def get_definition_by_object_id(self, object_id):
        definition = self.drawOpa.getByObjectID(object_id)
        if not definition:
            definition = self.drawXLU.getByObjectID(object_id)
        return definition

    # ------------------------------- Shaders -------------------------------------------
    def getShaders(self, material_list, for_modification=True):
        return self.shaders.getShaders(material_list, for_modification)

    # ----------------------------- Tex Links -------------------------------------
    def get_texture_link(self, name):
        for x in self.textureLinks:
            if x.name == name:
                return x

    def add_texture_link(self, name):
        if name != 'Null' and not self.parent.getTexture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AUTO_FIXER.info(notify, 4)

    def remove_texture_link(self, name):
        pass    # No longer applicable since tex links are rebuilt

    def rename_texture_link(self, layer, name):
        """Attempts to rename a layer, raises value error if the texture can't be found"""
        # No link found, try to find texture matching and create link
        if name != 'Null' and not self.parent.getTexture(name):
            tex = fuzzy_match(name, self.parent.textures)
            notify = 'Adding reference to unknown texture "{}"'.format(name)
            if tex:
                notify += ', did you mean ' + tex.name + '?'
            AUTO_FIXER.info(notify, 4)
        return name

    def getTrace(self):
        return self.parent.getTrace() + "->" + self.name

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
        sections = self.sections
        self.sections = None
        copy = super().__deepcopy__(memodict)
        self.sections = sections
        # relink things
        copy.sections = [copy.definitions, copy.bones, copy.vertices, copy.normals,
                         copy.colors, copy.texCoords, copy.furVectors, copy.furLayers,
                         copy.materials, copy.shaders, copy.objects,
                         copy.textureLinks, copy.paletteLinks]
        for x in copy.sections:
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
        self.shaders.updateName(material.name, new_name)
        return new_name

    def getTextureMap(self):
        return self.parent.get_texture_map()

    # --------------------------------------- Check -----------------------------------
    def check(self):
        """Checks model (somewhat) for validity
            texture_map: dictionary of tex_name:texture
        """
        super(Mdl0, self).check()
        texture_map = self.getTextureMap()
        for x in self.materials:
            x.check(texture_map)
        expected_name = self.parent.getExpectedMdl()
        if expected_name:
            if expected_name != self.name:
                b = Bug(2, 2, 'Model name does not match file', 'Rename to {}'.format(expected_name))
                if self.DETECT_MODEL_NAME:
                    if self.rename(expected_name):
                        b.resolve()
                        self.mark_modified()
            if expected_name == 'map':
                names = [x.name for x in self.bones]
                if 'posLD' not in names or 'posRU' not in names:
                    b = Bug(2, 2, 'Missing map model bones', 'Added map bones')
                    self.add_map_bones()
                    b.resolve()
                    self.mark_modified()
        self.checkDrawXLU()
        for x in self.texCoords:
            x.check()
        for x in self.vertices:
            x.check()

    def checkDrawXLU(self):
        count = 0
        for x in self.materials:
            is_draw_xlu = self.isMaterialDrawXlu(x.name)
            if x.xlu != is_draw_xlu:
                change = 'opa' if x.xlu else 'xlu'
                b = Bug(1, 4, '{} incorrect draw pass'.format(x.name), 'Change draw pass to {}'.format(change))
                if self.DRAW_PASS_AUTO:
                    if count == 0:
                        self.mark_modified()
                    count += 1
                    if x.xlu:
                        self.setMaterialDrawXlu(x.name)
                    else:
                        self.setMaterialDrawOpa(x.name)
                    b.resolve()
        return count

    def add_map_bones(self):
        current_names = [bone.name for bone in self.bones]
        parent = self.bones[0]
        minimum = self.minimum
        maximum = self.maximum
        if not 'posLD' in current_names:
            b = self.add_bone('posLD', parent)
            left = round(minimum[0] - 8000)
            down = round(maximum[2] + 8000)
            b.set_translation((left, 0, down))
        if not 'posRU' in current_names:
            b = self.add_bone('posRU', parent)
            right = round(maximum[0] + 8000)
            up = round(minimum[2] - 8000)
            b.set_translation((right, 0, up))


    def get_used_textures(self):
        textures = set()
        for x in self.materials:
            for y in x.layers:
                textures.add(y.name)
        return textures

    # ---------------START PACKING STUFF -------------------------------------
    def pre_pack(self):
        """Cleans up references in preparation for packing"""
        defs = [self.nodeTree, self.drawOpa, self.drawXLU]
        for x in self.sections[0]:
            if x not in defs:
                defs.append(x)
        defs = [x for x in defs if x]
        self.sections[0] = defs
        # rebuild texture links
        texture_links = {}
        for x in self.materials:
            for y in x.layers:
                name = y.name
                if name not in texture_links:
                    texture_links[name] = TextureLink(name, self)
                else:
                    texture_links[name].num_references += 1
        self.sections[11] = self.textureLinks = texture_links.values()

    def post_unpack(self):
        Bone.post_unpack(self.bones)


    def unpackSection(self, binfile, section_index):
        """ unpacks section by creating items  of type section_klass
            and adding them to section list index
        """
        # ignore fur sections for v8 mdl0s
        if section_index == 0:
            self.unpackDefinitions(binfile)
        elif section_index == 9:
            # assumes materials are unpacked..
            self.shaders.unpack(binfile, self.materials)
        elif binfile.recall():  # from offset header
            section_klass = self.SECTION_CLASSES[section_index]
            folder = Folder(binfile, self.SECTION_NAMES[section_index])
            folder.unpack(binfile)
            section = self.sections[section_index]
            while len(folder.entries):
                name = folder.recallEntryI()
                section.append(section_klass(name, self, binfile))
            return len(section)

    def unpackDefinitions(self, binfile):
        binfile.recall()
        folder = Folder(binfile, self.SECTION_NAMES[0])
        folder.unpack(binfile)
        found_xlu = found_opa = False
        while len(folder.entries):
            name = folder.recallEntryI()
            if 'Draw' in name:
                if 'Xlu' in name:
                    self.drawXLU = DrawList(name, self, binfile)
                    found_xlu = True
                elif 'Opa' in name:
                    self.drawOpa = DrawList(name, self, binfile)
                    found_opa = True
                else:
                    raise ValueError('Unknown Drawlist {}'.format(name))
            elif name == 'NodeTree':
                self.nodeTree = NodeTree(name, self, binfile)
            else:
                d = Definition(name, self, binfile)
                self.definitions.append(d)
        if not found_xlu:
            self.drawXLU = DrawList(Definition.names[1], self)
        if not found_opa:
            self.drawOpa = DrawList(Definition.names[0], self)

    def unpack(self, binfile):
        """ unpacks model data """
        self._unpack(binfile)
        offset = binfile.start()  # Header
        ln = binfile.readLen()
        fh, self.scaling_rule, self.texture_matrix_mode, self.facepoint_count, \
            self.faceCount, _, self.boneCount, _ = binfile.read("i7I", 32)
        binfile.store()  # bone table offset
        if binfile.offset - offset < ln:
            self.minimum = binfile.read("3f", 12)
            self.maximum = binfile.read("3f", 12)
        binfile.end()  # end header
        binfile.recallOffset(offset)
        self.boneTable = BoneTable()
        self.boneTable.unpack(binfile)
        # unpack sections
        i = 0
        while i < 14:
            if self.version < 10:
                if i == 6:
                    i += 2
                elif i == 13:
                    break
            self.unpackSection(binfile, i)
            i += 1
        binfile.end()  # end file
        self.post_unpack()

    def packTextureLinks(self, binfile, folder):
        """Packs texture link section, returning map of names:offsets be filled in by mat/layer refs"""
        tex_map = {}
        for x in self.textureLinks:
            folder.createEntryRefI()
            tex_map[x.name] = x.pack(binfile)
        return tex_map

    def pack_definitions(self, binfile, folder):
        for x in self.sections[0]:
            folder.createEntryRefI()
            x.pack(binfile)
        binfile.align(4)

    def pack_materials(self, binfile, folder, texture_link_map):
        """packs materials, requires texture link map to offsets that need to be filled"""
        for x in self.sections[8]:
            folder.createEntryRefI()
            x.pack(binfile, texture_link_map)
        for x in texture_link_map:
            if binfile.references[texture_link_map[x]]:
                raise PackingError(binfile, 'Unused texture link {}!'.format(x))

    def pack_shaders(self, binfile, folder):
        self.sections[9].pack(binfile, folder)

    def pack_section(self, binfile, section_index, folder):
        """ Packs a model section (generic) """
        section = self.sections[section_index]
        if section:
            # now pack the data
            for x in section:
                 if x:
                    folder.createEntryRefI()  # create reference to current data location
                    x.pack(binfile)

    def packFolders(self, binfile):
        """ Generates the root folders
            Does not hook up data pointers except the head group,
            returns rootFolders
        """
        root_folders = []  # for storing Index Groups
        sections = self.sections
        # Create folder for each section the MDL0 has
        i = j = 0
        while i < len(sections):
            section = sections[i]
            if i == 9:  # special case for shaders: must add entry for each material
                section = sections[i - 1]
            if section:
                f = Folder(binfile, self.SECTION_NAMES[i])
                for x in section:
                    if x:
                        f.addEntry(x.name)
                root_folders.append(f)
                binfile.createRef(j, False)  # create the ref from stored offsets
                f.pack(binfile)
            else:
                root_folders.append(None)  # create placeholder
            i += 1
            j += 1
        return root_folders

    def pack(self, binfile):
        """ Packs the model data """
        if self.sections[6] or self.sections[7] or self.sections[12]:
            raise PackingError(binfile, 'Packing Fur/palettes not supported')
        self.pre_pack()
        self._pack(binfile)
        binfile.start()  # header
        binfile.write("Ii7I", 0x40, binfile.getOuterOffset(), self.scaling_rule, self.texture_matrix_mode,
                      self.facepoint_count, self.faceCount, 0, self.boneCount, 0x01000000)
        binfile.mark()  # bone table offset
        if self.version >= 10:
            binfile.write("6f", self.minimum[0], self.minimum[1], self.minimum[2],
                          self.maximum[0], self.maximum[1], self.maximum[2])
        binfile.createRef()  # bone table
        self.boneTable.pack(binfile)
        binfile.end()  # end header
        # sections
        folders = self.packFolders(binfile)

        # texture links
        texture_link_map = self.packTextureLinks(binfile, folders[11])
        self.pack_definitions(binfile, folders[0])
        self.pack_section(binfile, 1, folders[1])  # bones
        i = 8
        self.pack_materials(binfile, folders[i], texture_link_map)
        i += 1
        self.pack_shaders(binfile, folders[i])
        i += 1
        self.pack_section(binfile, 10, folders[i])  # objects
        for i in range(2, 6):  # vertices, normals, colors, uvs
            self.pack_section(binfile, i, folders[i])
        binfile.alignAndEnd()  # end file
    # -------------- END PACKING STUFF ---------------------------------------
