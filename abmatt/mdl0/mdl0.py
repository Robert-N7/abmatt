""" MDL0 Models """
from matching import *
from mdl0.drawlist import DrawList, Definition
from mdl0.material import Material
from mdl0.shader import Shader, ShaderList
from subfile import SubFile
from binfile import *


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
    """ Links from materials to layers """

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.links = []

    def unpack(self, binfile):
        [length] = binfile.read("I", 4)
        for i in range(length):
            self.links.append(binfile.read("2i", 8))
            # todo: what does this actually do/how to rebuild

    def pack(self, binfile):
        binfile.write("I", len(self.links))
        for i in range(len(self.links)):
            binfile.write("2i", *self.links[i])


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
        super(Bone, self).__init__(name, parent)


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
                       FurLayer, Material, Shader, ModelObject, TextureLink, TextureLink)

    def __init__(self, name, parent):
        """ initialize with name and parent """
        super(Mdl0, self).__init__(name, parent)
        self.definitions = []
        self.drawXLU = None
        self.drawOpa = None
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

    def info(self, command, trace):
        trace += "->" + self.name
        if command.modelname or command.materialname:  # pass it down
            matching = findAll(command.materialname, self.materials)
            for m in matching:
                m.info(command, trace)
        else:
            if matches(command.name, self.name):
                print("{} Mdl0 {}:\t materials: {} shaders: {}".format(trace, self.version, len(self.materials),
                                                                       len(self.shaders)))
            # pass it along
            for x in self.materials:
                x.info(command, trace)

    # ---------------HOOK REFERENCES -----------------------------------------
    def hookSRT0ToMats(self, srt0):
        for animation in srt0.matAnimations:
            m = self.getMaterialByName(animation.name)
            if m:
                m.srt0 = animation

    # ---------------START PACKING STUFF -------------------------------------
    def unpackSection(self, binfile, section_index):
        """ unpacks section by creating items  of type section_klass
            and adding them to section list index
        """
        if section_index == 9:
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
        while len(folder.entries):
            name = folder.recallEntryI()
            if 'Draw' in name:
                d = DrawList(name, self)
                if 'Xlu' in name:
                    self.drawXLU = d
                elif 'Opa' in name:
                    self.drawOpa = d
            else:
                d = Definition(name, self)
            d.unpack(binfile)
            self.definitions.append(d)

    def unpack(self, binfile):
        """ unpacks model data """
        self._unpack(binfile)
        binfile.start() # Header
        ln, fh, _, _, self.vertexCount, self.faceCount, _, self.boneCount, _ = binfile.read("Ii7I", 36)
        binfile.store()  # bone table offset
        self.minimum = binfile.read("3f", 12)
        self.maximum = binfile.read("3f", 12)
        binfile.recall()
        self.boneTable = BoneTable()
        self.boneTable.unpack(binfile)
        binfile.end() # end header
        # unpack sections
        self.unpackDefinitions(binfile)
        for i in range(1, self._getNumSections()):
            self.unpackSection(binfile, i)
        binfile.end()  # end file

    def packSection(self, binfile, section_index, folder):
        """ Packs a model section """
        section = self.sections[section_index]
        if section_index == 9:
            section.pack(binfile, folder)
        elif section:
            print('Packing section {}'.format(self.SECTION_NAMES[section_index]))
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
        for i in range(len(sections)):
            section = sections[i]
            if i == 9:  # special case for shaders: must add entry for each material
                section = sections[i - 1]
            if section:
                f = Folder(binfile, self.SECTION_NAMES[i])
                for j in range(len(section)):
                    f.addEntry(section[j].name)
                root_folders.append(f)
                binfile.createRef(i, False) # create the ref from stored offsets
                f.pack(binfile)
            else:
                root_folders.append(None) # create placeholder
        return root_folders


    def pack(self, binfile):
        """ Packs the model data """
        if self.version != 11:
            raise ValueError("Unsupported mdl0 version {}".format(self.version))
        self._pack(binfile)
        binfile.start() # header
        binfile.write("Ii7I", 0x40, binfile.getOuterOffset(), 0, 0, self.vertexCount, self.faceCount,
                      0, self.boneCount, 0x01000000)
        binfile.mark()  # bone table offset
        binfile.write("6f", *self.minimum, *self.maximum)
        binfile.createRef() # bone table
        self.boneTable.pack(binfile)
        binfile.end() # end header
        # sections
        folders = self.packFolders(binfile)
        for i in self.SECTION_ORDER:
            self.packSection(binfile, i, folders[i])
        binfile.end()  # end file
    # -------------- END PACKING STUFF ---------------------------------------
