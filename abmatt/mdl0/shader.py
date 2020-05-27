# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from binfile import printCollectionHex
from bp import *

class Shader():
    BYTESIZE = 512
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.init_bp()

    def init_bp(self):
        ''' initializes blit processing commands '''
        self.bpmask0 = BPCommand(0xFE, 0xF)
        self.bpkcels = (BPCommand(0xF6, 0x4), BPCommand(0xF7, 0xE), BPCommand(0xF8, 0x0) \
                       BPCommand(0xF9, 0xC), BPCommand(0xFA, 0x5), BPCommand(0xFB, 0xD) \
                       BPCommand(0xFC, 0xA), BPCommand(0xFD, 0xE))
        self.ras1_Iref = RAS1_IRef()
        self.bpmask1 = BPCommand(0xFE, 0xFFFFF0)
        self.kcel1 = BPCommand(0xF6, 0x38c0)
        self.tref = BPCommand(0x28, 0x3BF040)
        self.color_env0 = BPCommand(0xC0, 0x18F8AF)
        self.color_env1 = BPCommand(0xC2, 0x088ff0, False)
        self.alpha_env0 = BPCommand(0xC1, 0x08F2F0)
        self.alpha_env1 = BPCommand(0xC3, 0x089f00, False)
        self.indirect0 = BPCommand(0x10)
        self.indirect1 = BPCommand(0x11, 0, False)



    def unpack(self, binfile):
        ''' Unpacks shader TEV '''
        binfile.start()
        len, outer, self.id, self.layercount, res0, res1, res2, = binfile.read("3I4B", 16)
        self.layerIndices = binfile.read("8B", 8)
        binfile.advance(8)
        for kcel in self.bpkcels:
            binfile.advance(5)  # skip extra masks
            kcel.unpack(binfile)
        self.ras1_Iref.unpack(binfile)
        binfile.align()
        self.tref.unpack(binfile)
        self.color_env0.unpack(binfile)
        self.color_env1.unpack(binfile)
        self.alpha_env0.unpack(binfile)
        self.alpha_env1.unpack(binfile)
        self.indirect0.unpack(binfile)
        self.indirect1.unpack(binfile)
        binfile.advanceAndEnd(self.BYTESIZE)


    def pack(self, binfile):
        ''' Packs the shader '''
        binfile.start()
        binfile.write("3I4B", self.BYTESIZE, binfile.getOuterOffset(), self.id, \
                      self.layercount, 0, 0, 0)
        binfile.write("8B", self.layerIndices)
        binfile.advance(8)
        for kcel in self.bpkcels:
            self.bpmask0.pack(binfile)
            kcel.pack(binfile)
        self.ras1_Iref.pack(binfile)
        binfile.align()
        self.tref.pack(binfile)
        self.color_env0.pack(binfile)
        self.color_env1.pack(binfile)
        self.alpha_env0.pack(binfile)
        self.alpha_env1.pack(binfile)
        self.indirect0.pack(binfile)
        self.indirect1.pack(binfile)
        binfile.advanceAndEnd(self.BYTESIZE)

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
