# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from struct import *

class Shader:
    def __init__(self, file, parent):
        self.parent = parent
        self.offset = file.offset
        data = file.read(Struct("> 3I 4B 8B 2I"), 0x20)
        self.length = data[0]
        self.mdl0Offset = data[1]
        self.id = data[2]
        self.layercount = data[3]
        self.res = data[4:7]
        self.references = data[7:15]
        # print("\t{}\tShader {} length {} layercount {}".format(self.offset, self.id, self.length, self.layercount))
        self.swapTable = file.read(Struct("> 80B"), 0x50)
        # print("Swap table: {}".format(self.swapTable))
        data = file.read(Struct("> 16B"), 16)
        # print("Data is {}".format(data))
        self.indirectTexMaps = []
        self.indirectTexCoords = []
        self.indirectTexMaps.append(data[4] & 7)
        self.indirectTexCoords.append(data[4] >> 3 & 7)
        self.indirectTexMaps.append(data[4] >> 6 & 3 | data[3] << 2 & 4)
        self.indirectTexCoords.append(data[3] >> 1 & 7)
        self.indirectTexMaps.append(data[3] >> 4 & 7)
        self.indirectTexCoords.append(data[3] >> 7 & 1 | data[2] << 1 & 6)
        self.indirectTexMaps.append(data[2] >> 2 & 7)
        self.indirectTexCoords.append(data[2] >> 5 & 7)
        data = file.read(Struct("> 384B"), 384)
        # print("Shader stage Data: {}".format(data))

    def __str__(self):
        return "shdr {} layers {} stages {}: {}".format(self.id, self.layercount, self.countDirectStages(), self.countIndirectStages())

    def countDirectStages(self):
        i = 0
        for x in self.references:
            # print("Ref {} is {}".format(i, x))
            if x > 7:
                break
            i+=1
        return i

    def countIndirectStages(self):
        i = 0
        for x in self.indirectTexMaps:
            if x >= 7:
                break
            i += 1
        return i


# possibly try to fix ctools bugs later
class TexCoord:
    TEX_FORMAT = ("u8", "s8", "u16", "s16", "float")
    def __init__(self, file):
        self.offset = file.offset
        data = file.read(Struct("> I i 5I 2B H 2f 2f"), 0x30)
        # print("Texture header: {}".format(data))
        self.length = data[0]
        self.mdl0Offset = data[1]
        self.dataOffset = data[2]
        self.nameOffset = data[3]
        self.id = data[4]
        self.component = data[5]
        self.format = data[6]
        self.divisor = data[7]
        self.stride = data[8]
        self.size = data[9]
        self.minimum = data[10:12]
        self.maximum = data[12:14]
        file.offset = self.offset + self.dataOffset
        data = file.read(Struct("> " + str(self.length - 0x30) + "B"), self.length - 0x30)
        # print("TCoord: {}".format(data))

    def __str__(self):
        return "UV {} size {} format {} divisor {} stride {}".format(self.id, self.size, self.TEX_FORMAT[self.format], self.divisor, self.stride)
