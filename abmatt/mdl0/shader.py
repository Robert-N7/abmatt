# ------------------------------------------------------------------------
#   Shader Class
# ------------------------------------------------------------------------
from binfile import printCollectionHex
from bp import *

class Stage():
    ''' Single shader stage '''
    # COLOR STRINGS
    RASTER_COLORS = ("lightchannel0", "lightchannel1", "bumpalpha", "normalizedbumpalpha", "zero")
    COLOR_CONSTANTS = ("1_1", "7_8", "3_4", "5_8", "1_2", "3_8", "1_4", "1_8",
                        "color0_rgb", "color1_rgb", "color2_rgb", "color3_rgb",
                        "color0_rrr", "color1_rrr", "color2_rrr", "color3_rrr",
                        "color0_ggg", "color1_ggg", "color2_ggg", "color3_ggg",
                        "color0_bbb", "color1_bbb", "color2_bbb", "color3_bbb",
                        "color0_aaa", "color1_aaa", "color2_aaa", "color3_aaa")
    COLOR_SELS = ("outputcolor", "outputalpha", "color0", "alpha0", "color1",
                  "alpha1", "color2", "alpha2", "texturecolor", "texturealpha",
                  "rastercolor", "rasteralpha", "one", "half",
                  "constantcolorselection", "zero")
    BIAS = ("zero", "addhalf", "subhalf")
    OPER = ("add", "subtract", "compr8greater", "compr8equal", "compgr16greater",
            "compgr16equal", "compbgr24greater", "compbgr24equal",
            "compa8greater", "compa8equal")
    SCALE = ("multiplyby1", "multiplyby2", "multiplyby4", "divideby2")
    SCALEN = (1, 2, 4, 1/2)
    COLOR_DEST = ("outputcolor", "color0", "color1", "color2")

    # ALPHA
    ALPHA_CONSTANTS = ("1_1", "7_8", "3_4", "5_8", "1_2", "3_8", "1_4", "1_8",
                       "color0_red", "color1_red", "color2_red", "color3_red",
                       "color0_green", "color1_green", "color2_green", "color3_green",
                       "color0_blue", "color1_blue", "color2_blue", "color3_blue",
                       "color0_alpha", "color1_alpha", "color2_alpha", "color3_alpha")
    ALPHA_SELS = ("outputalpha", "alpha0", "alpha1", "alpha2", "texturealpha",
                  "rasteralpha", "constantalphaselection", "zero")
    ALPHA_DEST = ("outputalpha", "alpha0", "alpha1", "alpha2")

    # INDIRECT TEVS
    TEX_FORMAT = ("f_8_bit_offsets", "f_5_bit_offsets", "f_4_bit_offsets", "f_3_bit_offsets")
    IND_BIAS = ("none", "s", "t", "st", "u", "su", "tu", "stu")
    IND_ALPHA = ("off", "s", "t", "u")
    IND_MATRIX = ("nomatrix", "matrix0", "matrix1", "matrix2", "matrixs0",
                  "matrixs1", "matrixs2", "matrixt0", "matrixt1", "matrixt2")
    WRAP = ("nowrap", "wrap256", "wrap128", "wrap64", "wrap16", "wrap0")

    def __init__(self, id):
        self.enabled = True
        self.mapID = id
        self.coordinateID = id
        self.texSwapSel = 0
        self.rasterColor = 0
        self.colorConstSel = 8
        self.colorA = -1
        self.colorB = 8
        self.colorC = 10
        self.colorD = -1
        self.colorBias = 0
        self.colorOper = 0
        self.colorClamp = True
        self.colorScale = 0
        self.colorDest = 0
        self.alphaConstSel = 20
        self.alphaA = -1
        self.alphaB = 4
        self.alphaC = 5
        self.alphaD = -1
        self.alphaBias = 0
        self.alphaOper = 0
        self.alphaClamp = True
        self.alphaScale = 0
        self.alphaDest = 0
        self.indStage = 0
        self.indFormat = 0
        self.indBias = 0
        self.indAlpha = 0
        self.indMatrix = 0
        self.swrawp = 0
        self.twrap = 0
        self.usePrevStage = False
        self.unmodifiedLOD = False

    def unpack(self, binfile):
        ''' Unpacks the shader stage '''
        pass
        
    def pack(self, binfile):
        ''' packs the shader stage '''
        pass

class Shader():
    BYTESIZE = 512
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.init_bp()

    def init_bp(self):
        ''' initializes blit processing commands '''
        self.bpmask0 = BPCommand(0xFE, 0xF)
        self.bpkcels = (BPCommand(0xF6, 0x4), BPCommand(0xF7, 0xE), BPCommand(0xF8, 0x0), \
                       BPCommand(0xF9, 0xC), BPCommand(0xFA, 0x5), BPCommand(0xFB, 0xD), \
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
        remaining = binfile.readRemaining(self.BYTESIZE)
        printCollectionHex(remaining)
        return
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
