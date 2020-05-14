#!/usr/bin/Python
#---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
#---------------------------------------------------------------------
import unpack
from struct import *

class Material:
    # CULL MODES
    CULL_NONE = 0
    CULL_OUTSIDE = 1
    CULL_INSIDE = 2
    CULL_ALL = 3
    # COMPARE
    COMP_NEVER = 0
    COMP_LESS = 1
    COMP_EQUAL = 2
    COMP_LESSOREQUAL = 3
    COMP_GREATER = 4
    COMP_NOTEQUAL = 5
    COMP_GREATEROREQUAL = 6
    COMP_ALWAYS = 7

    def __init__(self, name):
        self.isModified = False
        self.name = name.decode()
        self.layers = []
        self.lightChannels = []
        self.colors = []
        self.constantColors = []

    def unpack(self, file):
        self.offset = file.offset
        matData = file.read(Struct("> 5I 4B I 4B 4B 4B"), 40) #up to 0x20
        print("\t{} Name: {}, index: {}".format(self.offset, self.name, matData[3]))
        print("Flags: {}, texgens: {}, lights: {}, shaderstages: {}, indirectStages: {}".format(matData[4], matData[5], matData[6], matData[7], matData[8]))
        print("Cull: {}, CompareBeforeTexture: {}, Lightset: {}, Fogset: {}".format(matData[9], matData[10], matData[11], matData[12]))
        self.id = matData[3]
        self.xlu = matData[4]
        numTexGens = matData[5]
        # self.flags = ?
        self.cullmode = matData[9]
        self.compareBeforeTexture = matData[10]

        oset = file.offset
        matData = file.read(Struct("> 6I"), 24)
        print("{} Shader Offset {}, numTextures {}, layer offset {}".format(oset, matData[0], matData[1], matData[2]))
        # if self.version < 10:
        #     displayListOffset = matData[4]
        # else:
        #     displayListOffset = matData[5]

        # file.offset =  matData[0] + self.offset
        # self.unpack_shader(file)
        # Advance to layer offset
        file.offset = matData[2] + self.offset
        for i in range(matData[1]):
            ref = Layer(file)
            self.addLayer(ref)
        if file.offset % 0x20:
            file.offset += (0x20 - file.offset % 0x20)
        oset = file.offset
        mode = file.read(Struct("32B"), 32)
        print("\t{} MODE: {}".format(oset, mode))
        self.comp0 = mode[2] & 7
        self.comp1 = mode[2] >> 3 & 7
        self.logic = (mode[2] >> 6) & 3 # always 0 (and)
        self.ref1 = mode[3]
        self.ref0 = mode[4]
        depthfunction = mode[9]
        self.enableDepthTest = depthfunction & 1
        self.depthFunction = (depthfunction >> 1) & 0x7
        self.enableDepthUpdate = (depthfunction >> 4) & 1
        self.srcFactor = mode[18] & 7
        self.blendlogic = mode[18] >> 4 & 0xf
        self.dstFactor = mode[19] >> 5 & 7
        self.enableBlend = mode[19] & 1
        self.enableBlendLogic = mode[19] >> 1 & 1
        self.subtract = mode[19] >> 3 & 1
        self.constAlphaEnable = mode[23]
        oset = file.offset
        tev = file.read(Struct("128B"), 128)
        # A tev[2-3] R tev[4] G tev[7-8] B tev[9]
        # G and B are repeated 3 times for some reason
        j = 2
        for i in range(3):
            self.colors.append((tev[2 + j], (tev[5 + j] << 4) | (tev[6 + j] >> 4), tev[7 + j], (tev[j] << 4) | (tev[1 + j] >> 4)))
            j += 20
            print("Color: {}".format(self.colors[i]))
        j += 4
        for i in range(4):
            self.constantColors.append((tev[2 + j], ((tev[5 + j] & 0xf) << 4) | (tev[6 + j] >> 4), tev[7 + j], ((tev[j] & 0xf) << 4) | (tev[1 + j] >> 4)))
            j+=10
            print("Color: {}".format(self.constantColors[i]))
        print("\t{} Tev: {}".format(oset, tev))
        oset = file.offset
        shaderTex = file.read(Struct("64B"), 64)
        print("\t{} TexTransform: {}".format(oset, shaderTex))
        oset = file.offset
        xfFlags = file.read(Struct("160B"), 160)
        print("\t{} Matrices: {}".format(oset, xfFlags))
        j = 0
        # 18 width
        # byte 5-6 r-shifted 1 short emboss light
        # byte 7 msb 1-3 emboss source
        # 3 lsb and msb of 8 are coordinates (geometry 0 normals 1 colors 10 BinormalsT 11 BinormalsB 100 TexCoord0 101 TexCoord1 110 TexCoord2 111 TexCoord3 1000 TexCoord4 1001 TexCoord5 1010 TexCoord6 1011 TexCoord 7 1111)
        # byte 8 lsb bit 2 is projection (STU 1 ST 0)
        # bit 3 inputform (AB11 0 ABC1 1)
        # bit 5-6 type (regular 0 embossmap1 color0 10 color1 11)
        # byte 16 lsb normalize
        for i in range(len(self.layers)):
            layer = self.getLayer(i)
            layer.embossLight = (xfFlags[j + 5] << 8 | xfFlags[j + 6]) << 1 | (xfFlags[j + 7] >> 7 & 1)
            layer.embossSource = xfFlags[j + 7] >> 4 & 7
            layer.coordinates = xfFlags[j + 7] << 1 & 0xe | (xfFlags[j + 8] >> 7 & 1)
            layer.projection = xfFlags[j + 8] >> 1 & 1
            layer.inputform = xfFlags[j + 8] >> 2 & 1
            layer.type = xfFlags[j + 8] >> 4 & 3
            layer.normalize = xfFlags[j + 16]
            print("light {} source {} coordinates {} project {} inputform {} type {} normalize {}".format(layer.embossLight, layer.embossSource, layer.coordinates, layer.projection, layer.inputform, layer.type, layer.normalize))
            j += 18

        # for i in range(8):"
        #     shader = file.read(Struct("48B"), 48)
        #     print(shader)

        file.offset = self.offset + 0x1a8
        matData = file.read(Struct("< 4B I"), 8)
        layerIndex = 0
        for i in range(3, -1, -1): # read it backwards
            flags = matData[i]
            print("Layer Flags: {}".format(flags))
            layer = self.getLayer(layerIndex)
            if layer:
                layer.flags = flags & 0xf
            layerIndex += 1
            layer = self.getLayer(layerIndex)
            if layer:
                layer.flags = (flags >> 4)  & 0xf
            layerIndex += 1
        self.textureMatrixMode = matData[4]
        # print("Mat Flags {}".format(matData))
        # Texture Position
        matData = file.read(Struct("> 40f"), 160)
        structIndex = 0
        for i in range(8):
            layer = self.getLayer(i)
            if layer:
                layer.scale = (matData[structIndex], matData[structIndex + 1])
                layer.rotation = matData[structIndex + 2]
                layer.translation = (matData[structIndex + 3], matData[structIndex + 4])
                structIndex += 5
                print("Name: {}, Scale: {}, Rotation: {}, translation: {} flags: {}".format(layer.name, layer.scale, layer.rotation, layer.translation, hex(layer.flags)))
        # Texture Matrix
        for i in range(8):
            layer = self.getLayer(i)
            if layer:
                matData = file.read(Struct("> 4B 12f"), 52)
                layer.scn0CameraRef = matData[0]
                layer.scn0LightRef = matData[1]
                layer.mapMode = matData[2]
                layer.enableIdentityMatrix = matData[3]
                layer.textureMatrix = matData[4:]
            else:
                file.offset += 52
        # Lighting channels
        self.lightChannels.append(LightChannel(file))
        self.lightChannels.append(LightChannel(file))


    def addLayer(self, layer):
        self.layers.append(layer)

    def getLayer(self, i):
        if i < len(self.layers):
            return self.layers[i]
        return None

    def setTransparent(self):
        if not self.ref0 or self.comp0 == self.COMP_ALWAYS:
            self.ref0 = 128
            self.ref1 = 255
            self.comp0 = self.COMP_GREATEROREQUAL
            self.comp1 = self.COMP_LESSOREQUAL
        self.compareBeforeTexture = False
        self.xlu = True
        self.isModified = True

    def setOpaque(self):
        self.ref0 = 0
        self.ref1 = 0
        self.comp0 = self.COMP_ALWAYS
        self.comp1 = self.COMP_ALWAYS
        self.compareBeforeTexture = True
        self.xlu = False
        self.isModified = True

    # todo find the shader and update it
    def setShader(self, shader):
        self.shader = shader

    def setCullModeStr(self, cullstr):
        if "all" in cullstr:
            self.cullmode = self.CULL_ALL
        elif "inside" in cullstr:
            self.cullmode = self.CULL_INSIDE
        elif "outside" in cullstr:
            self.cullmode = self.CULL_OUTSIDE
        elif "none" in cullstr:
            self.cullmode = self.CULL_NONE
        else:
            raise ValueError("Invalid cullmode " + cullstr)
        self.isModified = True

    def setLightChannelStr(self, lcStr):
        enable = 1 if "vertex" in lcStr else 0
        self.lightChannels[0].setVertex(enable)
        self.isModified = True


class Layer:
    WRAP=["Clamp", "Repeat", "Mirror"]
    FILTER = ["Nearest", "Linear", "Nearest_Mipmap_Nearest", "Linear_Mipmap_Nearest", "Nearest_Mipmap_Linear", "Linear_Mipmap_Linear"]
    ANISOTROPHY = ["One", "Two", "Four"]
    def __init__(self, file):
        self.offset = file.offset
        layer = file.read(Struct("> 10I f I 4B"), 52)
        print("Layer: {}".format(layer))
        name = file.unpack_name(layer[0] + self.offset)
        self.name = name.decode()
        self.texDataID = layer[4]
        self.palleteDataID = layer[5]
        self.uwrap = self.WRAP[layer[6]]
        self.vwrap = self.WRAP[layer[7]]
        self.minFilter = self.FILTER[layer[8]]
        self.magFilter = self.FILTER[layer[9]]
        self.LODBias = layer[10]
        self.maxAnisotrophy = self.ANISOTROPHY[layer[11]]
        self.clampBias = layer[12]
        self.texelInterpolate = layer[13]


class Shader:
    def __init__(self, id):
        self.id = id
        self.stages = [ShaderStage()]

class ShaderStage:
    def __init__(self):
        self.textureMap = 0
        self.textureCoord = 0
        self.textureSwap = 0
        self.rasterColor = "LightChannel0"
        self.rasterSwap = 0
        self.colorConstant = "ConstantColor0"
        self.colorA = 0
        self.colorB = "TextureColor"
        self.colorC = "RasterColor"
        self.colorD = 0
        self.colorBias = 0
        self.colorOperation = "Add"
        self.colorClamp = True
        self.colorScale = "MultiplyBy2"
        self.colorDestination = "OutputColor"
        self.alphaConstant = "ConstantAlpha0"
        self.alphaA = 0
        self.alphaB = "TextureAlpha"
        self.alphaC = "RasterAlpha"
        self.alphaD = 0
        self.alphaBias = 0
        self.alphaOperation = "Add"
        self.alphaClamp = True
        self.alphaScale = "MultiplyBy1"
        self.alphaDestination = "OutputAlpha"
        self.indirectTextureMap = 0xff
        self.indirectTextureCoord = 0xff
        self.indirectBias = 0
        self.indirectMatrix = 0

# LIGHT CHANNEL ----------------------------------------------------
        # LC flags bits
        # 0	Material color enabled
        # 1	Material alpha enabled
        # 2	Ambient color enabled
        # 3	Ambient alpha enabled
        # 4	Raster color enabled
        # 5	Raster alpha enabled
# Light Controls
#   3rd byte 7 for activated, 4th 0-1 for ambient or vertex color
class LightChannel:
    def __init__(self, file):
        data = file.read(Struct("> 20B"), 20)
        print("Light Channel data {}".format(data))
        self.flags = data[3]
        self.materialColor = data[4:8]
        self.ambientColor = data[8:12]
        self.colorLightControl = data[12:16]
        self.alphaLightControl = data[16:20]

    def setVertex(self, vertexEnabled):
        self.colorLightControl[3] = 1 if vertexEnabled else 0
        self.alphaLightControl[3] = 1 if vertexEnabled else 0


class BlendMode:
    def __init__(self, enabled):
        self.enabled = enabled
        self.enableBlendLogic = False
        self.srcFactor = "SourceAlpha"
        self.blendLogicOp = "Copy"
        self.dstFactor = "InverseSourceAlpha"
        self.subtract = False
