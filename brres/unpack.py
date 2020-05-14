#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
# -------------------------------------------------------------------
from struct import *
import binascii
from material import *



class BinRead:
    def __init__(self, filename, container):
        self.container = container
        self.offset = 0
        file = open(filename, "rb")
        self.file = file.read()
        file.close()

    def read(self, struct, len):
        packed = self.file[self.offset:(self.offset + len)]
        self.offset += len
        return struct.unpack(packed)

    def readOffset(self, struct, offset, len):
        packed = self.file[offset:(offset + len)]
        return struct.unpack(packed)

    def unpack_name(self, offset):
        nameLens = self.readOffset(Struct("> I"), offset - 4, 4)
        if nameLens[0] > 120:
            print("Name length too long!")
        else:
            name = self.readOffset(Struct("> " + str(nameLens[0]) + "s"), offset, nameLens[0]);
            print("Name: {}".format(name[0]))
            return name[0]



class BresSubFile:
    structs = {
        "h" : Struct("> 4s I I I")
    }
    numSections = {
        "CHR03" : 1,
        "CHR05" : 5,
        "CLR04" : 2,
        "MDL08" : 11,
        "MDL011" : 14,
        "PAT04" : 6,
        "SCN04" : 6,
        "SCN05" : 7,
        "SHP04" : 3,
        "SRT04" : 1,
        "SRT05" : 2,
        "TEX01" : 1,
        "TEX02" : 2,
        "TEX03" : 1
    }
    def __init__(self, file, offset):
        self.offset = file.offset = offset
        self.h = file.read(self.structs["h"], 16)
        # print("Subfile, len, version, outerOffset: {}".format(self.h))
        self.magic = self.h[0]
        self.length = self.h[1]
        self.version = self.h[2]
        # self.bin = file.file[self.offset:self.offset + self.length]
        self.sectionCount = self.numSections[self.magic.decode() + str(self.version)]
        # print("section count: {}".format(self.sectionCount))
        self.sectionOffsets = file.read(Struct(">" + (" I" * self.sectionCount)), self.sectionCount * 4)
        # print("{} Section offsets: {}".format(self.magic, self.sectionOffsets))
        if self.magic == b"MDL0":
            UnpackMDL0(file, self)


class IndexGroup:
    structs = {
        "h" : Struct("> I I"),
        "indexGroup" : Struct("> H H H H I I"),
    }
    def __init__(self, file, offset):
        if offset:
            file.offset = offset
        self.startOffset = file.offset
        self.h = file.read(self.structs["h"], 8)
        print("Group byte len, numEntries: {}".format(self.h))
        self.entries = []
        self.entryNames = []
        self.entryOffsets = []
        # file.offset += 16
        for i in range(self.h[1] + 1):
            entry = file.read(self.structs["indexGroup"], 16)
            print("Entry id, uk, left, right, namep, datap {}".format(entry))
            if i != 0:
                name = file.unpack_name(entry[4] + self.startOffset)
                self.entryNames.append(name)
                self.entryOffsets.append(entry[5] + self.startOffset)
            # else:
            #     self.entryNames.append("Null")

            self.entries.append(entry)


class UnpackMDL0:
    def __init__(self, file, subFileHeader):
        print("======================================================================")
        print("\t\tMDL0:")
        self.file = file
        self.offset = subFileHeader.offset
        self.version = subFileHeader.version
        self.indexGroups = []
        self.sections = []
        self.drawlistsGroup = None
        self.bonesGroup = None
        self.verticesGroup = None
        self.normalsGroup = None
        self.colorsGroup = None
        self.texCoordGroup = None
        self.furVectorsGroup = None
        self.furlayersGroup = None
        self.materialsGroup = None
        self.tevsGroup = None
        self.objectsGroup = None
        self.palettelinksGroup = None
        self.texturelinksGroup = None
        self.folders = subFileHeader
        offsets =  subFileHeader.sectionOffsets
        for i in range(len(offsets)):
            group = None
            if offsets[i]: # offset exists?
                print("Section {} exists".format(i))
                if i == 0:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.drawlistsGroup = group
                elif i == 1:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.bonesGroup = group
                elif i == 2:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.verticesGroup = group
                elif i == 3:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.normalsGroup = group
                elif i == 4:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.colorsGroup = group
                elif i == 5:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.texCoordGroup = group
                elif i == 6:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.furVectorsGroup = group
                elif i == 7:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.furlayersGroup = group
                elif i == 8:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.materialsGroup = group
                elif i == 9:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.tevsGroup = group
                elif i == 10:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.objectsGroup = group
                elif i == 11:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.texturelinksGroup = group
                elif i == 12:
                    group = IndexGroup(file, offsets[i] + self.offset)
                    self.palettelinksGroup = group
            self.indexGroups.append(group)
        # Header file
        file.offset = self.offset + 0x14 + (self.version + 3) * 4
        self.h = file.read(Struct("> 4I 6I 3f 3f"), 64)
        file.offset = self.h[9] + self.offset
        self.boneTable = self.unpack_boneTable(file)
        self.mats = self.unpack_materials(file)
        self.drawlists = self.unpack_drawlists(file)
        self.bones = self.unpack_bones(file)
        self.vertices = self.unpack_vertices(file)
        self.normals = self.unpack_normals(file)
        self.colors = self.unpack_colors(file)
        self.texCoords = self.unpack_textureCoordinates(file)
        self.furVectors = self.unpack_furVectors(file)
        self.furLayers = self.unpack_furLayers(file)
        self.tevs = self.unpack_tevs(file)
        self.objects = self.unpack_objects(file)
        self.textureLinks = self.unpack_texturelinks(file)
        self.paletteLinks = self.unpack_palletelinks(file)
        self.sections.append(self.drawlists)
        self.sections.append(self.bones)
        self.sections.append(self.vertices)
        self.sections.append(self.normals)
        self.sections.append(self.colors)
        self.sections.append(self.texCoords)
        self.sections.append(self.furVectors)
        self.sections.append(self.furLayers)
        self.sections.append(self.mats)
        self.sections.append(self.tevs)
        self.sections.append(self.objects)
        self.sections.append(self.textureLinks)
        self.sections.append(self.paletteLinks)
        # for i in range(len(self.sections)):
        #     section = self.sections[i]
        #     if section:
        #         entryNames = self.indexGroups[i].entryNames
        #         offsets = self.indexGroups[i].entryOffsets
        #         print("=========================================================================")
        #         print("Section {}:\tsize {}".format(i, len(section)))
        #         print("=========================================================================")
        #         for i in range(len(section)):
        #             print("{} {}\t{}".format(offsets[i], entryNames[i], section[i]))
        #     else:
        #         print("------------------------------Missing section-----------------------------")
        print("======================================================================")
        file.container.models.append(self)

    def unpack_boneTable(self, file):
        count = file.read(Struct("> I"), 4)
        return file.read(Struct(">" + str(count[0]) + "I"), 4 * count[0])

    def unpack_drawlists(self, file):
        if not self.drawlistsGroup:
            return None
        offsets = self.drawlistsGroup.entryOffsets
        drawlists = []
        maxOffsetlist = len(offsets)
        for i in range(maxOffsetlist):
            done = False
            struct0 = Struct("> B")
            struct1 = Struct("> 4B")
            struct2 = Struct("> 7B")
            currentList = []
            file.offset = offsets[i]
            while not done:
                byte = file.read(struct0, 1)
                # print("Byte: {}".format(byte))
                currentList.append(byte[0])
                if byte[0] == 0x01:
                    break
                elif byte[0] == 0x02 or byte[0] == 0x05:
                    currentList.append(file.read(struct1, 4))
                else:
                    currentList.append(file.read(struct2, 7))
            drawlists.append(currentList)
        return drawlists

    def unpack_bones(self, file):
        if not self.bonesGroup:
            return None
        offsets = self.bonesGroup.entryOffsets
        print(offsets)
        bones = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            bones.append(file.read(Struct("> 8I 9f 6f 5I 12f 12f"), 0xd0))
            # todo children bones?
        return bones

    def unpack_vertices(self, file):
        if not self.verticesGroup:
            return None
        offsets = self.verticesGroup.entryOffsets
        vertices = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            vertices.append(file.read(Struct("> 7I 2B H 3f 3f"), 0x38))
        return vertices

    def unpack_normals(self, file):
        if not self.normalsGroup:
            return None

        offsets = self.normalsGroup.entryOffsets
        normals = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            normals.append(file.read(Struct("> 7I 2B H"), 0x20))
        return normals

    def unpack_colors(self, file):
        if not self.colorsGroup:
            return None

        offsets = self.colorsGroup.entryOffsets
        colors = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            colors.append(file.read(Struct("> 7I 2B H"), 0x20))
        return colors

    def unpack_textureCoordinates(self, file):
        if not self.texCoordGroup:
            return None

        offsets = self.texCoordGroup.entryOffsets
        texCoord = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            texCoord.append(file.read(Struct("> 7I 2B H 2f 2f"), 0x30))
        return texCoord


    def unpack_furVectors(self, file):
        if not self.furVectorsGroup:
            return None
        offsets = self.furVectorsGroup.entryOffsets
        fv = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            fv.append(file.read(Struct("> 5I H 10B"), 0x20))
        return fv

    def unpack_furLayers(self, file):
        if not self.furlayersGroup:
            return None
        offsets = self.furlayersGroup.entryOffsets
        layers = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            layers.append(file.read(Struct("> 7I 2B H 3f 3f"), 0x38))
        return layers

    def unpack_materials(self, file):
        mats = []
        offsets = self.materialsGroup.entryOffsets
        names = self.materialsGroup.entryNames
        storedOffset = self.offset
        for i in range(len(offsets)):
            file.offset = offsets[i]
            mat = Material(names[i])
            mat.unpack(file)
            mats.append(mat)
        return mats

    def unpack_shader(self, file):
        # todo sort this mess out
        modeInformation = file.read(Struct("> 32B"), 32)
        shaderID = modeInformation[11]
        numStages = modeInformation[12]
        # print("\tID: {} NumStages: {}".format(shaderID, numStages))
        # print("Shader Header: {}".format(modeInformation))
        tevRegs = file.read(Struct("> 80B"), 80)
        # print("\tTevRegs: {}".format(tevRegs))
        indirectRefs = file.read(Struct("> 16B"), 16)
        # for i in range(8):
        #     textureTransformations = file.read(Struct("> 48B"), 48)
        #     # textureTransformations = file.read(Struct("> 32B"), 32)
        #     print("\tstage {}: {}".format(i, textureTransformations))
        #     if i == 0:
        #         offset = 5
        #         print("Data {}, {} at offset {}".format(textureTransformations[offset], hex(textureTransformations[offset]), offset))
        # textureMatrices = file.read(Struct("> 160B"), 160)
        # print("\tmatrices: {}".format(textureMatrices))

    def unpack_tevs(self, file):
        if not self.tevsGroup:
            return None
        offsets = self.tevsGroup.entryOffsets
        tevs = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            tevs.append(file.read(Struct("> 3I 4B 8B 2I"), 0x20))
        return tevs

    def unpack_objects(self, file):
        if not self.objectsGroup:
            return None
        offsets = self.objectsGroup.entryOffsets
        objects = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            objects.append(file.read(Struct("> 18I 2H 10H 2I"), 0x68))
        return objects

    def unpack_texturelinks(self, file):
        if not self.texturelinksGroup:
            return None
        offsets = self.texturelinksGroup.entryOffsets
        tlinks = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            size = file.read(Struct("> I"), 4)
            tlinks.append(file.read(Struct("> " + str(size[0] * 2) + "I"), size[0] * 8))
        return tlinks

    def unpack_palletelinks(self, file):
        if not self.palettelinksGroup:
            return None
        offsets = self.palettelinksGroup.entryOffsets
        palletelinks = []
        for i in range(len(offsets)):
            file.offset = offsets[i]
            size = file.read(Struct("> I"), 4)
            palletelinks.append(file.read(Struct("> " + str(size[0] * 2) + "I"), size[0] * 8))
        return palletelinks



class UnpackBrres:
    structs = {
        "h" : Struct("> 4s H H I H H"),
        "root" : Struct("> 4s I"),
        "indexGroupH" : Struct("> I I"),
        "indexGroup" : Struct("> H H H H I I"),
    }

    def __init__(self, filename):
        print("Starting...")
        structs = self.structs
        self.models = []
        self.textures = []
        self.anmClr = []
        self.anmTexSrt = []
        f = BinRead(filename, self)
        self.file = f
        brresHd = f.read(structs["h"], 16)
        print("Unpacked: {}".format(brresHd))
        # assert(brresHd[0] == "bres")
        f.offset = brresHd[4]

        self.brresHd = brresHd
        self.rootHd = f.read(structs["root"], 8)
        print("Unpacked: {}".format(self.rootHd))
        self.indexGroups = []
        self.subFiles = []
        self.root = IndexGroup(f, 0)
        for offset in self.root.entryOffsets:
            self.indexGroups.append(IndexGroup(f, offset))
        for group in self.indexGroups:
            # folderNames = group.entryNames
            offsets = group.entryOffsets
            for i in range(len(offsets)):
                # print("\t=====Folder {}======".format(folderNames[i]))
                self.subFiles.append(BresSubFile(f, offsets[i]))
        self.structs = structs
        self.filename = filename
