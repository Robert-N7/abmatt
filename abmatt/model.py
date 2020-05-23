''' MDL0 Models '''
from material import Material
from shader import Shader
from subfile import SubFile
from bin import *

#----------------- Model sub files --------------------------------------------
class ModelGeneric:
    ''' A generic model class - most data structures have similar type of header'''

    def __init__(self, name, hasDataptr=True, hasNamePtr=True):
        ''' flags:  l = length, m = mdl0Offset, d = data offset, n = nameoffset, i = index
            if flag is present must be in order
        '''
        self.hasDataptr = hasDataptr
        self.hasNamePtr = hasNamePtr
        self.name = name

    def unpack(self, bin):
        ''' Unpacks some ptrs but mostly just leaves data as bytes '''
        bin.start()
        self.length, mdl = bin.read("Ii", 8)
        if self.hasDataptr:
            self.dataPtr = bin.read("I", 4)
        if self.hasNamePtr:
            bin.advance(4)   # ignore, we already have name
        self.index = bin.read("I", 4)
        # doesn't do much unpacking
        self.data = bin.readRemaining(self.length)
        bin.end()

    def pack(self, bin):
        ''' Packs into bin '''
        bin.start()
        bin.write("Ii", 8, self.length, bin.getOuterOffset())
        if self.hasDataptr:
            bin.write("I", 4, self.dataPtr)
        if self.hasNamePtr:
            bin.storeNameRef(self.name)
        bin.write("I", 4, self.index)
        bin.writeRemaining(self.data)
        bin.end()

class TextureLink:
    ''' Links from materials to layers '''
    def __init__(self):
        self.links = []

    def unpack(self, bin):
        length = bin.read("I", 4)
        for i in range(length):
            self.links.append(bin.read("2I", 8))
            # todo: what does this actually do/how to rebuild

    def pack(self, bin):
        bin.write("I", 4, len(self.links))
        for i in range(len(self.links)):
            bin.write("2I", 8, self.links[i])

class ModelObject(ModelGeneric):
    ''' Object model data '''
    def __init__(self, name):
        super.__init__(name, False, False)

class FurLayer(ModelGeneric):
    ''' Fur Layer model data '''
    def __init__(self, name):
        super.__init__(name)

class FurVector(ModelGeneric):
    ''' Fur Vector model data '''
    def __init__(self, name):
        super.__init__(name)

class TexCoord(ModelGeneric):
    ''' TexCoord model data'''
    def __init__(self, name):
        super.__init__(name)

class Color(ModelGeneric):
    ''' Colors model data '''
    def __init__(self, name):
        super.__init__(name)

class Normal(ModelGeneric):
    ''' Normals model data '''
    def __init__(self, name):
        super.__init__(name)

class Vertex(ModelGeneric):
    ''' Vertex class for storing vertices data '''
    def __init__(self, name):
        super.__init__(name)

class Bone(ModelGeneric):
    ''' Bone class '''
    def __init__(self, name):
        super().__init(name, False)

class BoneTable:
    ''' Bonetable class '''
    def unpack(self, bin):
        ''' unpacks bonetable '''
        length = bin.read("I", 4)
        self.entries = bin.read("{}I".format(length), length * 4)

    def pack(self, bin):
        length = len(self.entries)
        bin.write("I", 4, length)
        bin.write("{}I".format(length), length * 4, self.entries)

class DrawList:
    ''' Drawlist, controls drawing commands such as opacity'''
    names = ["drawOpa", "drawXlu", "mixNode", "boneTree"] # todo check these
    def __init__(self, name):
        self.name = name
        self.list = []

    def unpack(self, bin):
        ''' unpacks draw list '''
        currentList = self.list
        while True:
            [byte] = bin.read("B", 1)
            currentList.append(byte)
            if byte == 0x01: # end list
                break
            elif byte == 0x4:
                currentList.append(bin.read("7B", 7))
            elif byte == 0x3:
                weightId, weigthCount, tableId = bin.read("3H", 6)
                bytes = 4 * weigthCount
                weights = bin.read("{}B".format(bytes), bytes) # not sure if these are ints
                drawl = [weightId, weigthCount, tableId] + list(weights)
                currentList.append(drawl)
            elif byte > 0x6: # error reading list?
                print("Error unpacking list {}".format(currentList))
                break
            else:
                currentList.append(bin.read("4B", 4))

    def pack(self, bin):
        ''' packs the draw list '''
        for i in range(len(self.list)):
            x = self.list[i]
            if i % 2 == 0: # cmd
                bin.write("B", 1, x)
            else:   # list
                bin.write("{}B".format(len(x)), len(x), x)

# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
class Model(SubFile):
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
        super().__init__(name, parent)
        self.drawlists = []
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
        self.sections = [self.drawlists, self.bones, self.vertices, self.normals,
                         self.colors, self.texCoords, self.furVectors, self.furLayers,
                         self.materials, self.shaders, self.objects,
                         self.textureLinks, self.paletteLinks]

    def info(self, command, trace):
        trace += "->" + self.name
        if command.modelname or command.materialname: # pass it down
            matching = findAll(command.materialname, self.mats)
            for m in matching:
                m.info(command, trace)
        else:
            if matches(command.name, self.name):
                print("{} Mdl0 {}:\t Mats: {} shaders: {}".format(trace, self.version, len(self.mats), len(self.tevs)))
            # pass it along
            for x in self.mats:
                x.info(command, trace)


    #---------------START PACKING STUFF -------------------------------------
    def unpackSection(self, bin, sectionKlass, sectionIndex):
        ''' unpacks section by creating items  of type sectionKlass
            and adding them to section list index
        '''
        if bin.recallParent(): # from offset header
            folder = Folder(bin, self.SECTION_NAMES[sectionIndex])
            folder.unpack()
            section = self.sections[sectionIndex]
            while len(folder.entries):
                name = folder.recallEntryI()
                d = sectionKlass(name)
                d.unpack(bin)
                section.append(d)
            return len(section)

    def unpackData(self, bin):
        ''' unpacks model data '''
        bin.start()
        # Header
        len, fh, _, _, self.vertexCount, self.faceCount, _, self.boneCount, _  = bin.read("Ii7I", 36)
        bin.store() # bone table offset
        self.minimum = bin.read("3f", 12)
        self.maximum = bin.read("3f", 12)
        bin.recall()
        self.boneTable = BoneTable()
        self.boneTable.unpack(bin)
        # unpack sections
        for i in range(self.getNumSections()):
            self.unpackSection(bin, i)
        bin.end()

    def packSection(self, bin, sectionIndex):
        ''' Packs a model section '''
        section = self.sections[sectionIndex]
        if section:
            bin.createParentRef(sectionIndex, False)
            # Create index group
            folder = Folder(bin, self.SECTION_NAMES[sectionIndex])
            for x in section:
                folder.addEntry(x.name)
            folder.pack()
            # now pack the data
            for x in section:
                folder.createEntryRefI() # create reference to current data location
                x.pack()

    def packData(self, bin):
        ''' Packs the model data '''
        if self.version != 11:
            raise ValueError("Unsupported mdl0 version {}".format(self.version))
        bin.start()
        # header
        fileoffset = (self.getNumSections() * 4 + 0x14) * -1
        bin.write("Ii7I", 36, 0x40, fileoffset, 0, 0, self.vertexCount, self.faceCount,
                  0, self.boneCount, 0)
        bin.mark() # bone table offset
        bin.write("6f", 24, self.minimum, self.maximum)
        bin.createRef()
        self.boneTable.pack(bin)
        # sections
        for i in self.SECTION_ORDER:
            self.packSection(bin, i)
        bin.end()
    #-------------- END PACKING STUFF ---------------------------------------
