""" MDL0 Models """
from abmatt.binfile import Folder
from abmatt.drawlist import DrawList, Definition
from abmatt.matching import findAll
from abmatt.material import Material
from abmatt.polygon import Polygon
from abmatt.shader import Shader, ShaderList
from abmatt.subfile import SubFile


# ----------------- Model sub files --------------------------------------------
class ModelGeneric(object):
    """ A generic model class - most data structures have similar type of header"""

    def __init__(self, name, parent, has_data_ptr=True, has_name_ptr=True):
        """ Each model subfile has len, mdloffset, [dataptr], [nameptr], index"""
        self.parent = parent
        self.hasDataptr = has_data_ptr
        self.hasNamePtr = has_name_ptr
        self.name = name

    def unpack(self, binfile):
        """ Unpacks some ptrs but mostly just leaves data as bytes """
        binfile.start()
        self.length, mdl = binfile.read("Ii", 8)
        offset = binfile.beginOffset + mdl
        if self.hasDataptr:
            [self.dataPtr] = binfile.read("I", 4)
        if self.hasNamePtr:
            binfile.advance(4)  # ignore, we already have name
        [self.index] = binfile.read("I", 4)
        # doesn't do much unpacking
        self.data = binfile.readRemaining(self.length)
        binfile.end()

    def pack(self, binfile):
        """ Packs into binfile """
        binfile.start()
        binfile.write("Ii", self.length, binfile.getOuterOffset())
        if self.hasDataptr:
            binfile.write("I", self.dataPtr)
        if self.hasNamePtr:
            binfile.storeNameRef(self.name)
        binfile.write("I", self.index)
        binfile.writeRemaining(self.data)
        binfile.end()


class TextureLink:
    """ Links from textures to materials and layers """

    def __init__(self, name, parent=None):
        """Only tracks number of references, which serve as placeholders to be filled in by the layers"""
        self.name = name
        self.parent = parent
        self.num_references = 0

    def __bool__(self):
        return self.num_references > 0

    def unpack(self, binfile):
        binfile.start()
        [self.num_references] = binfile.read("I", 4)
        for i in range(self.num_references):    # ignore this?
            link = binfile.read("2i", 8)
        binfile.end()

    def pack(self, binfile):
        offset = binfile.start()
        binfile.write("I", self.num_references)
        for i in range(self.num_references):
            binfile.mark(2)  # marks 2 references
        binfile.end()
        return offset


class ModelObject(ModelGeneric):
    """ Object model data """

    def __init__(self, name, parent=None):
        super(ModelObject, self).__init__(name, parent, False, False)


class FurLayer(ModelGeneric):
    """ Fur Layer model data """

    def __init__(self, name, parent=None):
        super(FurLayer, self).__init__(name, parent)


class FurVector(ModelGeneric):
    """ Fur Vector model data """

    def __init__(self, name, parent):
        super(FurVector, self).__init__(name, parent)


class TexCoord(ModelGeneric):
    """ TexCoord model data"""

    def __init__(self, name, parent):
        super(TexCoord, self).__init__(name, parent)


class Color(ModelGeneric):
    """ Colors model data """

    def __init__(self, name, parent):
        super(Color, self).__init__(name, parent)


class Normal(ModelGeneric):
    """ Normals model data """

    def __init__(self, name, parent):
        super(Normal, self).__init__(name, parent)


class Vertex(ModelGeneric):
    """ Vertex class for storing vertices data """

    def __init__(self, name, parent):
        super(Vertex, self).__init__(name, parent)


class Bone(ModelGeneric):
    """ Bone class """
    def __init__(self, name, parent):
        super(Bone, self).__init__(name, parent, False)


class BoneTable:
    """ Bonetable class """

    def unpack(self, binfile):
        """ unpacks bonetable """
        [length] = binfile.read("I", 4)
        self.entries = binfile.read("{}I".format(length), length * 4)

    def pack(self, binfile):
        length = len(self.entries)
        binfile.write("I", length)
        binfile.write("{}I".format(length), *self.entries)


# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
class Mdl0(SubFile):
    """ Model Subfile """
    MAGIC = "MDL0"
    VERSION_SECTIONCOUNT = {8: 11, 11: 14}
    SECTION_NAMES = ("Definitions", "Bones", "Vertices", "Normals", "Colors",
                     "UVs", "FurVectors", "FurLayers",
                     "Materials", "Shaders", "Objects", "Textures", "Palettes")

    SECTION_ORDER = (11, 0, 1, 6, 7, 8, 9, 10, 2, 3, 4, 5)

    SECTION_CLASSES = (DrawList, Bone, Vertex, Normal, Color, TexCoord, FurVector,
                       FurLayer, Material, Shader, Polygon, TextureLink, TextureLink)

    def __init__(self, name, parent):
        """ initialize with name and parent """
        super(Mdl0, self).__init__(name, parent)
        self.drawXLU = DrawList('DrawXlu', self)
        self.drawOpa = DrawList('DrawOpa', self)
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

    def getMaterialsByName(self, name):
        return findAll(name, self.materials)

    def getShaders(self, material_list, for_modification=True):
        return self.shaders.getShaders(material_list, for_modification)

    def getMaterialByName(self, name):
        """Exact naming"""
        for m in self.materials:
            if m.name == name:
                return m
        return None

    def getMaterialByID(self, id):
        for x in self.materials:
            if x.id == id:
                return x

    def getTextureLink(self, name):
        for x in self.textureLinks:
            if x.name == name:
                return x

    def addLayerReference(self, name):
        link = self.getTextureLink(name)
        if not link:
            if name != 'Null' and not self.parent.getTexture(name):
                print('WARNING: Adding reference to unknown texture "{}"'.format(name))
            link = TextureLink(name, self)
            self.textureLinks.append(link)
        link.num_references += 1

    def removeLayerReference(self, name):
        link = self.getTextureLink(name)
        if not link:
            raise ValueError('No such texture link: {}'.format(name))
        link.num_references -= 1

    def renameLayer(self, layer, name):
        """Attempts to rename a layer, raises value error if the texture can't be found"""
        # first try to get texture link
        old_link = new_link = None
        for x in self.textureLinks:
            if x.name == name:
                new_link = x
            if x.name == layer.name:
                old_link = x
        assert(old_link)
        # No link found, try to find texture matching and create link
        if not new_link:
            if name != 'Null' and not self.parent.getTexture(name):  # possible todo, regex matching for name?
                print('WARNING: Adding reference to unknown texture "{}"'.format(name))
            new_link = TextureLink(name, self)
            self.textureLinks.append(new_link)
        old_link.num_references -= 1
        new_link.num_references += 1
        return name

    def getTrace(self):
        return self.parent.getTrace() + "->" + self.name

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
        definition = self.drawXLU.getByMaterialID(material_id)
        if not definition:
            definition = self.drawOpa.getByMaterialID(material_id)
        return definition.getPriority()

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>' + self.name if indentation_level else self.parent.name + "->" + self.name
        print("{}:\t{} material(s)\t{} shader(s)".format(trace, len(self.materials),
                                                                   len(self.shaders)))
        indentation_level += 1
        # pass it along
        for x in self.materials:
            x.info(key, indentation_level)
        for x in self.shaders:
            x.info(key, indentation_level)

    # ---------------HOOK REFERENCES -----------------------------------------
    def hookSRT0ToMats(self, srt0):
        for animation in srt0.matAnimations:
            m = self.getMaterialByName(animation.name)
            if m:
                m.srt0 = animation
                animation.material = m
            else:
                print('Unknown animation reference "{}"'.format(animation.name))

    def check(self):
        for x in self.materials:
            x.check()

    def checkDrawXLU(self):
        count = 0
        for x in self.materials:
            is_draw_xlu = self.isMaterialDrawXlu(x.id)
            if x.xlu != is_draw_xlu:
                if count == 0:
                    self.parent.isModified = True
                count += 1
                mark = 'xlu' if x.xlu else 'opa'
                print('Note: Fixing incorrect draw pass for {}, marking as {}'.format(x.name, mark))
                if x.xlu:
                    self.setMaterialDrawXlu(x.id)
                else:
                    self.setMaterialDrawOpa(x.id)
        return count

    # ---------------START PACKING STUFF -------------------------------------
    def clean(self):
        """Cleans up references in preparation for packing"""
        self.definitions = [x for x in self.definitions if x]
        self.shaders.consolidate()
        self.textureLinks = [x for x in self.textureLinks if x.num_references > 0]
        parent = self.parent
        for x in self.textureLinks:
            if not parent.getTexture(x.name):
                print('WARNING: Texture Reference "{}" not found.'.format(x.name))
        self.check()

    def unpackSection(self, binfile, section_index):
        """ unpacks section by creating items  of type section_klass
            and adding them to section list index
        """
        # ignore fur sections for v8 mdl0s
        if section_index == 0:
            self.unpackDefinitions(binfile)
        elif section_index == 9:
            # assumes materials are unpacked.. possible bug?
            self.shaders.hookMatsToShaders(self.shaders.unpack(binfile), self.materials)
        elif binfile.recall():  # from offset header
            section_klass = self.SECTION_CLASSES[section_index]
            folder = Folder(binfile, self.SECTION_NAMES[section_index])
            folder.unpack(binfile)
            section = self.sections[section_index]
            while len(folder.entries):
                name = folder.recallEntryI()
                d = section_klass(name, self)
                d.unpack(binfile)
                section.append(d)
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
                    d = self.drawXLU
                    found_xlu = True
                    if not found_opa:
                        self.definitions.append(self.drawOpa) # empty but it might change
                elif 'Opa' in name:
                    d = self.drawOpa
                    found_opa = True
                else:
                    d = DrawList(name, self)
            else:
                d = Definition(name, self)
            d.unpack(binfile)
            self.definitions.append(d)
        if not found_xlu:
            self.definitions.append(self.drawXLU)   # empty but might change

    def unpack(self, binfile):
        """ unpacks model data """
        self._unpack(binfile)
        binfile.start()  # Header
        ln, fh, _, _, self.vertexCount, self.faceCount, _, self.boneCount, _ = binfile.read("Ii7I", 36)
        binfile.store()  # bone table offset
        if binfile.offset - binfile.beginOffset < ln:
            self.minimum = binfile.read("3f", 12)
            self.maximum = binfile.read("3f", 12)
        binfile.recall()
        self.boneTable = BoneTable()
        self.boneTable.unpack(binfile)
        binfile.end()  # end header
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
        self.checkDrawXLU()

    def packTextureLinks(self, binfile, folder):
        """Packs texture link section, returning map of names:offsets be filled in by mat/layer refs"""
        tex_map = {}
        for x in self.textureLinks:
            folder.createEntryRefI()
            tex_map[x.name] = x.pack(binfile)
        return tex_map

    def packSection(self, binfile, section_index, folder, extras=None):
        """ Packs a model section """
        section = self.sections[section_index]
        if section_index == 9:
            section.pack(binfile, folder)
        elif section_index == 8:
            for x in section:
                folder.createEntryRefI()
                x.pack(binfile, extras)
        elif section:
            # now pack the data
            for x in section:
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
            if i == 6 and self.version < 10:
                i += 2
            section = sections[i]
            if i == 9:  # special case for shaders: must add entry for each material
                section = sections[i - 1]
            if section:
                f = Folder(binfile, self.SECTION_NAMES[i])
                for k in range(len(section)):
                    f.addEntry(section[k].name)
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
        self.clean()
        self._pack(binfile)
        binfile.start()  # header
        binfile.write("Ii7I", 0x40, binfile.getOuterOffset(), 0, 0, self.vertexCount, self.faceCount,
                      0, self.boneCount, 0x01000000)
        binfile.mark()  # bone table offset
        if self.version >= 10:
            binfile.write("6f", self.minimum[0], self.minimum[1], self.minimum[2],
                          self.maximum[0], self.maximum[1], self.maximum[2])
        binfile.createRef()  # bone table
        self.boneTable.pack(binfile)
        binfile.end()  # end header
        # sections
        folders = self.packFolders(binfile)
        texture_link_map = None
        for i in self.SECTION_ORDER:
            folder = folders[i - 2] if i > 5 and self.version < 10 else folders[i]
            if i == 11:     # special case for texture links
                texture_link_map = self.packTextureLinks(binfile, folder)
            else:
                self.packSection(binfile, i, folder, texture_link_map)
        binfile.end()  # end file
    # -------------- END PACKING STUFF ---------------------------------------
