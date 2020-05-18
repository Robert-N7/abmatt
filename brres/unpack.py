#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
# -------------------------------------------------------------------
from struct import *
import binascii
from material import *
from shader import *



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
    def __init__(self, file, offset, name):
        self.offset = file.offset = offset
        self.name = name
        self.h = file.read(self.structs["h"], 16)
        # print("Subfile, len, version, outerOffset: {}".format(self.h))
        self.magic = self.h[0]
        self.length = self.h[1]
        self.version = self.h[2]
        # self.bin = file.file[self.offset:self.offset + self.length]
        self.sectionCount = self.numSections[self.magic.decode() + str(self.version)]
        # print("section count: {}".format(self.sectionCount))
        self.sectionOffsets = file.read(Struct("> " + str(self.sectionCount) + "I" ), self.sectionCount * 4)
        # print("{} Section offsets: {}".format(self.magic, self.sectionOffsets))
        if self.magic == b"MDL0":
            Model(file, self)
