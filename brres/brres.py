#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
# -------------------------------------------------------------------
from struct import *
import binascii

class BinRead:
    def __init__(self, filename):
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
    def __init__(self, file):
        self.offset = file.offset
        self.h = file.read(self.structs["h"], 16)
        print("Unpacked: {}".format(self.h))
        self.magic = self.h[0]
        self.length = self.h[1]
        self.version = self.h[2]
        self.bin = file.file[self.offset:self.offset + self.length]
        self.sectionCount = self.numSections[self.magic + str(self.version)]
        print("Got section count of {}".format(self.sectionCount))
        self.sectionOffsets = file.read(Struct(">" + (" I" * self.sectionCount)), self.sectionCount * 4)
        print("{} Section offsets: {}".format(self.magic, self.sectionOffsets))


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
        print("Unpacked: {}".format(self.h))
        self.entries = []
        self.entryNames = []
        self.entryOffsets = []
        # file.offset += 16
        for i in range(self.h[1] + 1):
            entry = file.read(structs["indexGroup"], 16)
            print("Unpacked: {}".format(entry))
            if i != 0:
                nameLenst = file.readOffset(structs["entryNameLen"], entry[4] - 4 + self.startOffset, 4)
                nameLen = nameLenst[0]
                # print("Name length: {}".format(nameLen))
                name = file.readOffset(Struct("> " + str(nameLen) + "s"), entry[4] + self.startOffset, nameLen);
                print("Name: {}".format(name[0]))
                self.entryNames.append(name)
                self.entryOffsets.append(entry[5] + self.startOffset)
            self.entries.append(entry)
        self.children = []
        if not offset:
            for off in self.entryOffsets:
                self.children.append(IndexGroup(file, off))
        else:
            for off in self.entryOffsets:
                file.offset = off
                self.children.append(BresSubFile(file))



class Brres:
    def __init__(self, filename):
        structs = {
            "h" : Struct("> 4s H H I H H"),
            "root" : Struct("> 4s I"),
            "indexGroupH" : Struct("> I I"),
            "indexGroup" : Struct("> H H H H I I"),
        }
        print("Starting...")
        f = BinRead(filename)
        brresHd = f.read(structs["h"], 16)
        print("Unpacked: {}".format(brresHd))
        assert(brresHd[0] == "bres")
        f.offset = brresHd[4]
        self.brresHd = brresHd
        self.rootHd = f.read(structs["root"], 8)
        print("Unpacked: {}".format(self.rootHd))
        self.indexGroups = []
        self.indexGroups.append(IndexGroup(f, 0))
        self.structs = structs
        self.filename = filename



b = Brres("course_model.brres")
