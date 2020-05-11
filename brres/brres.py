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
        print("Subfile, len, version, outerOffset: {}".format(self.h))
        self.magic = self.h[0]
        self.length = self.h[1]
        self.version = self.h[2]
        # self.bin = file.file[self.offset:self.offset + self.length]
        self.sectionCount = self.numSections[self.magic + str(self.version)]
        # print("section count: {}".format(self.sectionCount))
        self.sectionOffsets = file.read(Struct(">" + (" I" * self.sectionCount)), self.sectionCount * 4)
        print("{} Section offsets: {}".format(self.magic, self.sectionOffsets))
        if self.magic == "MDL0":
            UnpackMDL0(file, self)


class IndexGroup:
    def __init__(self, file, offset):
        structs = {
            "h" : Struct("> I I"),
            "indexGroup" : Struct("> H H H H I I"),
            "entryNameLen" : Struct("> I")
        }
        if offset:
            file.offset = offset
        self.startOffset = file.offset
        self.h = file.read(structs["h"], 8)
        print("Group byte len, numEntries: {}".format(self.h))
        self.entries = []
        self.entryNames = []
        self.entryOffsets = []
        # file.offset += 16
        for i in range(self.h[1] + 1):
            entry = file.read(structs["indexGroup"], 16)
            print("Entry id, uk, left, right, namep, datap {}".format(entry))
            if i != 0:
                nameLens = file.readOffset(structs["entryNameLen"], entry[4] - 4 + self.startOffset, 4)
                nameLen = nameLens[0]
                if nameLen > 120:
                    print("Name length too long!")
                else:
                    # print("Name length: {}".format(nameLen))
                    name = file.readOffset(Struct("> " + str(nameLen) + "s"), entry[4] + self.startOffset, nameLen);
                    print("Name: {}".format(name[0]))
                    self.entryNames.append(name[0])
                    self.entryOffsets.append(entry[5] + self.startOffset)
            # else:
            #     self.entryNames.append("Null")

            self.entries.append(entry)


class UnpackMDL0:
    def __init__(self, file, subFileHeader):
        print("======================================================================")
        print("\t\tMDL0:")
        self.offset = subFileHeader.offset
        self.version = subFileHeader.version
        self.indexGroups = []
        self.folders = subFileHeader
        offsets =  subFileHeader.sectionOffsets
        for i in range(len(offsets)):
            if offsets[i]: # offset exists?
                if i == 0:
                    self.drawlistsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 1:
                    self.bonesGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 2:
                    self.verticesGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 3:
                    self.normalsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 4:
                    self.colorsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 5:
                    self.texCoordGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 6:
                    self.furVectorsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 7:
                    self.furlayersGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 8:
                    self.materialsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 9:
                    self.tevsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 10:
                    self.objectsGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 11:
                    self.texturelinksGroup = IndexGroup(file, offsets[i] + self.offset)
                elif i == 12:
                    self.palettelinksGroup = IndexGroup(file, offsets[i] + self.offset)
        # Header file
        file.offset = self.offset + 0x14 + (self.version + 3) * 4
        self.h = file.read(Struct("> 4I I I I I I I 3f 3f"), 64)
        file.container.models.append(self)
        self.unpack_materials(file)
        print("======================================================================")

    def unpack_materials(self, file):
        mats = []
        offsets = self.materialsGroup.entryOffsets
        names = self.materialsGroup.entryNames
        for i in range(len(offsets)):
            mat = Material(names[i])
            file.offset = offsets[i]
            matData = file.read(Struct("> 5I 4B I 4B 4B 4B"), 40) #up to 0x20
            print("\tName: {}, index: {}".format(names[i], matData[3]))
            print("Flags: {}, texgens: {}, lights: {}, shaderstages: {}, indirectTex: {}".format(matData[4], matData[5], matData[6], matData[7], matData[8]))
            print("Cull: {}, AlphaFunction: {}, Lightset: {}, Fogset: {}".format(matData[9], matData[10], matData[11], matData[12]))
            mat.xlu = matData[4]
            numTexGens = matData[5]
            mat.cullmode = matData[9]
            if matData[10]:
                mat.setTransparent()
            matData = file.read(Struct("> 3I"), 12)
            print("Shader Offset {}, numTextures {}, layer offset {}".format(matData[0], matData[1], matData[2]))
            file.offset = offsets[i] + 0x1a8
            matData = file.read(Struct("< 4B I"), 8)
            for i in range(3, -1, -1): # read it backwards
                if i & 1:
                    
            print("Read {}".format(matData))
            matData = file.read(Struct("> 40f"), 160)
            print("Scale: {},{}, Rotation: {}, translation: {}, {}".format(matData[0], matData[1], matData[2], matData[3], matData[4]))



class Brres:
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
        brresHd = f.read(structs["h"], 16)
        print("Unpacked: {}".format(brresHd))
        assert(brresHd[0] == "bres")
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


b = Brres("course_model.brres")
