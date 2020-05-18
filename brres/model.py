# ---------------------------------------------------------------------
#   Model class
# ---------------------------------------------------------------------
from material import *
from layer import *
from shader import *
from struct import *
from pack import *
from unpack import *
from fileobject import *
from brres import *

class IndexGroup:
    structs = {
        "h" : Struct("> I I"),
        "indexGroup" : Struct("> H H H H I I"),
    }
    def __init__(self, file, offset):
        if offset:
            file.offset = offset
        self.isModified = False
        self.offset = file.offset
        self.h = file.read(self.structs["h"], 8)
        # print("Group byte len, numEntries: {}".format(self.h))
        self.entries = []
        self.entryNames = []
        self.entryOffsets = []
        # file.offset += 16
        for i in range(self.h[1] + 1):
            entry = file.read(self.structs["indexGroup"], 16)
            # if self.h[1] == 3:
            # print("{} Entry id, uk, left, right, namep, datap {}".format(file.offset - 16, entry))
            if i != 0:
                name = file.unpack_name(entry[4] + self.offset)
                self.entryNames.append(name)
                self.entryOffsets.append(entry[5] + self.offset)
            # else:
            #     self.entryNames.append("Null")

            self.entries.append(entry)

    def updateEntryOffset(self, offset, index):
        self.entryOffsets[index] = offset
        self.isModified = True

    # does not handle changing left right id etc
    def repack(self, file):
        if not self.isModified:
            return
        offset = self.offset
        # pack header
        pack_into("> I I", file.file, offset, self.h[0], self.h[1])
        offset += 8
        # pack entries
        for i in range(len(self.entries)):
            entry = self.entries[i]
            entryOffset = entry[5] if i == 0 else self.entryOffsets[i - 1] - self.offset
            # print("Offset is {} for entry {}".format(self.offset + entryOffset, self.entries[i]))
            pack_into("> 4H 2I", file.file, offset, entry[0], entry[1], entry[2],
            entry[3], entry[4], entryOffset)
            offset += 16


class Model:
    def __init__(self, file, subFileHeader):
        # print("======================================================================")
        self.file = file
        self.isModified = False
        self.offset = subFileHeader.offset
        self.version = subFileHeader.version
        if self.version != 11:
            raise ValueError("Unsupported mdl0 version {}".format(self.version))
        self.name = subFileHeader.name.decode()
        # print("\t\tMDL0: {}".format(self.name))
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
                # print("Section {} exists".format(i))
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
        #         print("Section {}:\tsize {} offset {}".format(i, len(section), offsets[0]))
        #         print("=========================================================================")
        #         for j in range(len(section)):
        #             print("{} {}\t{}".format(offsets[j], entryNames[j], section[j]))
        #     else:
        #         print("------------------------------Missing section-----------------------------")
        # print("======================================================================")
        file.container.models.append(self)

    def isChanged(self):
        if self.isModified:
            return True
        for mat in self.mats:
            if mat.isChanged():
                self.isModified = True
                return True
        return False

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
        # print(offsets)
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
            texCoord.append(TexCoord(file))
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
            mat = Material(names[i], file, self)
            mats.append(mat)
        return mats

    # updates the associated shader entry with the material
    def updateTevEntry(self, tev, material):
        self.tevsGroup.updateEntryOffset(tev.offset, material.id)


    def getTev(self, index):
        for x in self.tevs:
            if x.id == index:
                return x
        return None

    def unpack_tevs(self, file):
        if not self.tevsGroup:
            return None
        offsets = self.tevsGroup.entryOffsets
        used = []
        tevs = []
        for i in range(len(offsets)):
            if not offsets[i] in used:
                file.offset = offsets[i]
                used.append(file.offset)
                tev = Shader(file)
                tevs.append(tev)
        for tev in tevs:
            for mat in self.mats:
                if tev.offset == mat.shaderOffset + mat.offset:
                    mat.setShader(tev)
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
