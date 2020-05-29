''' MDL0 Models '''
from material import Material
from matching import *
from mdl0.drawlist import DrawList, Definition
from shader import Shader
from subfile import SubFile
from binfile import *

#----------------- Model sub files --------------------------------------------
class ModelGeneric(object):
    ''' A generic model class - most data structures have similar type of header'''

    def __init__(self, name, parent, hasDataptr=True, hasNamePtr=True):
        ''' Each model subfile has len, mdloffset, [dataptr], [nameptr], index'''
        self.parent = parent
        self.hasDataptr = hasDataptr
        self.hasNamePtr = hasNamePtr
        self.name = name

    def unpack(self, binfile):
        ''' Unpacks some ptrs but mostly just leaves data as bytes '''
        binfile.start()
        self.length, mdl = binfile.read("Ii", 8)
        if self.hasDataptr:
            [self.dataPtr] = binfile.read("I", 4)
        if self.hasNamePtr:
            binfile.advance(4)   # ignore, we already have name
        [self.index] = binfile.read("I", 4)
        if __debug__:
            print("Subfile Len {} outer file {} index {}".format(self.length,
                    mdl, self.index))
        # doesn't do much unpacking
        self.data = binfile.readRemaining(self.length)
        binfile.end()

    def pack(self, binfile):
        ''' Packs into binfile '''
        binfile.start()
        binfile.write("Ii", self.length, binfile.getOuterOffset())
        if self.hasDataptr:
            binfile.write("I", self.dataPtr)
        if self.hasNamePtr:
            binfile.storeNameRef(self.name)
        binfile.write("I", self.index)
        binfile.writeRemaining(self.data)
        binfile.end()

class TextureLink():
    ''' Links from materials to layers '''
    def __init__(self, name, parent = None):
        self.name = name
        self.parent = parent
        self.links = []

    def unpack(self, binfile):
        [length] = binfile.read("I", 4)
        for i in range(length):
            self.links.append(binfile.read("2I", 8))
            # todo: what does this actually do/how to rebuild

    def pack(self, binfile):
        binfile.write("I", len(self.links))
        for i in range(len(self.links)):
            binfile.write("2I", self.links[i])

class ModelObject(ModelGeneric):
    ''' Object model data '''
    def __init__(self, name, parent = None):
        super(ModelObject, self).__init__(name, parent, False, False)

class FurLayer(ModelGeneric):
    ''' Fur Layer model data '''
    def __init__(self, name, parent = None):
        super(FurLayer, self).__init__(name, parent)

class FurVector(ModelGeneric):
    ''' Fur Vector model data '''
    def __init__(self, name, parent):
        super(FurVector, self).__init__(name, parent)

class TexCoord(ModelGeneric):
    ''' TexCoord model data'''
    def __init__(self, name, parent):
        super(TexCoord, self).__init__(name, parent)

class Color(ModelGeneric):
    ''' Colors model data '''
    def __init__(self, name, parent):
        super(Color, self).__init__(name, parent)

class Normal(ModelGeneric):
    ''' Normals model data '''
    def __init__(self, name, parent):
        super(Normal, self).__init__(name, parent)

class Vertex(ModelGeneric):
    ''' Vertex class for storing vertices data '''
    def __init__(self, name, parent):
        super(Vertex, self).__init__(name, parent)

class Bone(ModelGeneric):
    ''' Bone class '''
    def __init__(self, name, parent):
        super(Bone, self).__init__(name, False)

class BoneTable:
    ''' Bonetable class '''
    def unpack(self, binfile):
        ''' unpacks bonetable '''
        [length] = binfile.read("I", 4)
        self.entries = binfile.read("{}I".format(length), length * 4)

    def pack(self, binfile):
        length = len(self.entries)
        binfile.write("I", length)
        binfile.write("{}I".format(length), length * 4, self.entries)



# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
class Mdl0(SubFile):
    ''' Model Subfile '''
    MAGIC = "MDL0"
    VERSION_SECTIONCOUNT = {8:11, 11:14}
    SECTION_NAMES = ("Definitions", "Bones", "Vertices", "Normals", "Colors",
                     "UVs", "FurVectors", "FurLayers",
                     "Materials", "Shaders", "Objects", "Textures", "Palettes")

    SECTION_ORDER = (11, 0, 1, 6, 7, 8, 9, 10, 2, 3, 4, 5)

    SECTION_CLASSES = (DrawList, Bone, Vertex, Normal, Color, TexCoord, FurVector,
                       FurLayer, Material, Shader, ModelObject, TextureLink, TextureLink)

    def __init__(self, name, parent):
        ''' initialize with name and parent '''
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
        self.shaders = []
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

    def info(self, command, trace):
        if __debug__:
            print("MODEL INFO CALLED {}".format(self.name))
        trace += "->" + self.name
        if command.modelname or command.materialname: # pass it down
            matching = findAll(command.materialname, self.materials)
            for m in matching:
                m.info(command, trace)
        else:
            if matches(command.name, self.name):
                print("{} Mdl0 {}:\t materials: {} shaders: {}".format(trace, self.version, len(self.materials), len(self.shaders)))
            # pass it along
            for x in self.materials:
                x.info(command, trace)

    #---------------HOOK REFERENCES -----------------------------------------
    def hookSRT0ToMats(self, srt0):
        for animation in srt0.matAnimations:
            m = self.getMaterialByName(animation.name)
            if m:
                m.srt0 = animation

    def hookShadersToMats(self):
        for x in self.shaders:
            mat = self.getMaterialByName(x.name)
            mat.shader = x
            x.material = mat

    #---------------START PACKING STUFF -------------------------------------
    def unpackSection(self, binfile, sectionIndex):
        ''' unpacks section by creating items  of type sectionKlass
            and adding them to section list index
        '''
        if binfile.recallParent(): # from offset header
            sectionKlass = self.SECTION_CLASSES[sectionIndex]
            folder = Folder(binfile, self.SECTION_NAMES[sectionIndex])
            folder.unpack(binfile)
            if __debug__:
                print("Unpacking section {} of mdl0 {} with {} entries".format(self.SECTION_NAMES[sectionIndex], self.name, len(folder)))
            section = self.sections[sectionIndex]
            while len(folder.entries):
                name = folder.recallEntryI()
                if __debug__:
                    print("Unpacking {} in section {}".format(name, sectionIndex))
                d = sectionKlass(name, self)
                d.unpack(binfile)
                section.append(d)
            return len(section)

    def unpackDefinitions(self, binfile):
        binfile.recallParent()
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
        ''' unpacks model data '''
        self._unpack(binfile)
        binfile.start()
        # Header
        if __debug__:
            print("Unpacking model data")
        len, fh, _, _, self.vertexCount, self.faceCount, _, self.boneCount, _  = binfile.read("Ii7I", 36)
        binfile.store() # bone table offset
        self.minimum = binfile.read("3f", 12)
        self.maximum = binfile.read("3f", 12)
        binfile.recall()
        self.boneTable = BoneTable()
        self.boneTable.unpack(binfile)
        # unpack sections
        self.unpackDefinitions(binfile)
        for i in range(1, self._getNumSections()):
            self.unpackSection(binfile, i)
        binfile.end()
        binfile.end()   # end file

    def packSection(self, binfile, sectionIndex):
        ''' Packs a model section '''
        section = self.sections[sectionIndex]
        if section:
            binfile.createParentRef(sectionIndex, False)
            # Create index group
            folder = Folder(binfile, self.SECTION_NAMES[sectionIndex])
            for x in section:
                folder.addEntry(x.name)
            folder.pack()
            # now pack the data
            for x in section:
                folder.createEntryRefI() # create reference to current data location
                x.pack()

    def packData(self, binfile):
        ''' Packs the model data '''
        if self.version != 11:
            raise ValueError("Unsupported mdl0 version {}".format(self.version))
        self._pack(binfile)
        # header
        fileoffset = (self.getNumSections() * 4 + 0x14) * -1
        binfile.write("Ii7I", 0x40, fileoffset, 0, 0, self.vertexCount, self.faceCount,
                  0, self.boneCount, 0)
        binfile.mark() # bone table offset
        binfile.write("6f", self.minimum, self.maximum)
        binfile.createRef()
        self.boneTable.pack(binfile)
        # sections
        for i in self.SECTION_ORDER:
            self.packSection(binfile, i)
        binfile.end()
        binfile.end()   # end file
    #-------------- END PACKING STUFF ---------------------------------------
