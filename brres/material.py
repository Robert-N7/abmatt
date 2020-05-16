#!/usr/bin/Python
#---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
#---------------------------------------------------------------------
import unpack
from struct import *

def validBool(str):
    if str == "false" or not str or str == "0" or str == "disable":
        return False
    elif str == "true" or str == "1" or str == "enable":
        return True
    raise ValueError("Not a boolean '" + str + "', expected true|false")

# finds index of item, if it is equal to compare index returns -1
# raises error if not found
def indexListItem(list, item, compareIndex):
    for i in range(len(list)):
        if list[i] == item:
            if i != compareIndex:
                return i
            else:
                return -1
    raise ValueError("Invalid setting '" + item + "', Options are: " + list)

def parseValStr(value):
    if value[0] == "(" and value[-1] == ")":
        value = value[1:-1]
    return value.split(",")

class Material:
    SETTINGS = ["xlu", "transparent", "ref0", "ref1", #4
    "comp0", "comp1", "comparebeforetexture", "blend", #8
    "blendsrc", "blendlogic", "blenddest", "constantalpha",
    "cullmode", "shader", "shadercolor", "lightchannel", #16
    "lightset", "fogset", "matrixmode", "enabledepthtest",
    "enabledepthupdate", "depthfunction", "drawpriority"] #23
    # CULL MODES
    CULL_STRINGS = ["none", "outside", "inside", "all"]
    # COMPARE
    COMP_STRINGS = ["never", "less", "equal", "lessorequal", "greater", "notequal", "greaterorequal", "always"]
    COMP_NEVER = 0
    COMP_LESS = 1
    COMP_EQUAL = 2
    COMP_LESSOREQUAL = 3
    COMP_GREATER = 4
    COMP_NOTEQUAL = 5
    COMP_GREATEROREQUAL = 6
    COMP_ALWAYS = 7
    # Blend factor
    BLLOGIC_STRINGS = ["clear", "and", "reverseand", "copy",
    "inverseand", "nooperation", "exclusiveor", "or", "notor", "equivalent", "inverse",
    "reverseor", "inversecopy", "inverseor", "notand", "set"]
    BLFACTOR_STRINGS = ["zero", "one", "sourcecolor", "inversesourcecolor",
     "sourcealpha", "inversesourcealpha", "destinationalpha", "inversedestinationalpha"]
    BLFACTOR_ZERO = 0
    BLFACTOR_ONE = 1
    BLFACTOR_SOURCECOLOR = 2
    BLFACTOR_INVERSESOURCECOLOR = 3
    BLFACTOR_SOURCEALPHA = 4
    BLFACTOR_INVERSESOURCEALPHA = 5
    BLFACTOR_DESTINATIONALPHA = 6
    BLFACTOR_INVERSEDESTINATIONALPHA = 7
    # Matrix mode
    MATRIXMODE_MAYA = 0
    MATRIXMODE_XSI = 1
    MATRIXMODE_3DSMAX = 2
    SHADERCOLOR_ERROR = "Invalid color '{}', Expected [constant]color<i>=<r>,<g>,<b>,<a>"

    def __init__(self, name):
        self.isModified = False
        self.name = name.decode()
        self.layers = []
        self.lightChannels = []
        self.colors = []
        self.constantColors = []

    def pack(self, file):
        if not self.isChanged():
            return
        data = file.file
        args = (self.length, self.mdl0Offset, self.nameOffset,
        self.id, self.xlu << 31, self.numLayers, self.numLights, self.shaderStages,
        self.indirectStages, self.cullmode, self.compareBeforeTexture, self.lightset,
        self.fogset)
        # print("===========> Packing mat flags at {}:\n{}".format(self.offset, data[self.offset:31 + self.offset]))
        pack_into("> 5I 4B I 3B", data, self.offset, *args)
        # print("{}".format(data[self.offset:31 + self.offset]))
        # Alpha Mode
        byte1 = self.logic << 6 | self.comp1 << 3 | self.comp0
        # print("===========> Packing alpha func at {}:\n{}".format(self.modeOffset + 2, data[self.modeOffset + 2: self.modeOffset + 5]))
        pack_into("> 3B", data, self.modeOffset + 2, byte1, self.ref1, self.ref0)
        # print("{}".format(data[self.modeOffset + 2:self.modeOffset+5]))
        offset = self.modeOffset + 9
        byte1 = data[offset] & 0xE0 | self.enableDepthUpdate << 4 | self.depthFunction << 1 | self.enableDepthTest
        # print("===========> Packing depth function at {}".format(offset))
        pack_into("> B", data, offset, byte1)
        offset = self.modeOffset + 18
        byte1 = self.blendlogic << 4 | self.srcFactor
        byte2 =  self.dstFactor << 5 | self.subtract << 3 | self.enableBlendLogic << 1 | self.enableBlend
        # print("===========> Packing blend logic at {}".format(offset))
        pack_into("> 2B", data, offset, byte1, byte2)
        # print("===========> Packing const alpha at {}".format(offset + 5))
        pack_into("> 2B", data, offset + 5, self.constAlphaEnable, self.constAlpha)
        offset = self.modeOffset + 34
        # print("===========> Packing colors at {}".format(offset))
        for i in range(3):
            color = self.colors[i]
            byte1 = color[3] >> 4 & 0x0f | data[offset] & 0xf0
            byte2 = color[3] << 4 & 0xf0 | data[offset + 1] & 0x0f
            # # print("Prev: {}\nCurr: {} {} {}".format(data[offset: offset + 3], hex(byte1), hex(byte2), hex(color[0])))
            pack_into("> 3B", data, offset, byte1, byte2, color[0])
            byte1 = color[1] >> 4 & 0x0f | data[offset + 5] & 0xf0
            byte2 = color[1] << 4 & 0xf0 | data[offset + 6] & 0x0f
            pack_into("> 3B", data, offset + 5, byte1, byte2, color[2])
            offset += 20
        offset += 4
        for i in range(4):
            color = self.constantColors[i]
            byte1 = color[3] >> 4 & 0xf | data[offset] & 0xf0
            byte2 = color[3] << 4 & 0xf0 | data[offset + 1] & 0xf
            # # print("Prev: {}\nCurr: {} {}".format(data[offset: offset + 2], hex(byte1), hex(byte2)))
            pack_into("> 3B", data, offset, byte1, byte2, color[0])
            byte1 = color[1] >> 4 & 0xf | data[offset + 5]  & 0xf0
            byte2 = color[1] << 4 & 0xf0 | data[offset + 6] & 0xf
            pack_into("> 3B", data, offset + 5, byte1, byte2, color[2])
            offset+=10
        # layers
        # xf flags
        file.offset = self.modeOffset + 0xe5
        # print("===========> Packing xfFlags at {}".format(file.offset))
        for i in range(len(self.layers)):
            self.layers[i].pack_xfFlags(file)
            file.offset += 18
        # texref
        file.offset = self.layerOffset + self.offset
        # print("===========> Packing layer at {}".format(file.offset))
        for i in range(len(self.layers)):
            # print("{} Before: {}".format(file.offset, data[file.offset:file.offset+32]))
            self.layers[i].pack_texRef(file)
            # print("{} Afterr: {}".format(file.offset, data[file.offset:file.offset+32]))
            file.offset += 52
        # layer flags
        offset = self.offset + 0x1a8
        layerIndex = 0
        # print("===========> Packing layer flags at {}".format(offset))
        for i in range(3, -1, -1): # read it backwards
            layer = self.getLayer(layerIndex)
            if layer:
                flags = layer.enable | layer.scaleFixed << 1 | layer.rotationFixed << 2 | layer.translationFixed << 3
            else:
                flags = 0
            layerIndex += 1
            layer = self.getLayer(layerIndex)
            if layer:
                flags = flags | (layer.enable | layer.scaleFixed << 1 | layer.rotationFixed << 2 | layer.translationFixed << 3) << 4
            pack_into("> B", data, offset + i, flags)
            layerIndex += 1
        offset += 4
        pack_into("> B", data, offset, self.textureMatrixMode)
        offset += 4
        # print("===========> Packing layer/scale/rotation at {}".format(offset))
        # layer scale / Rotation
        for layer in self.layers:
            # # print("{} Before: {}".format(offset, data[offset:offset+20]))
            pack_into("> 5f", data, offset, layer.scale[0], layer.scale[1], layer.rotation,
            layer.translation[0], layer.translation[1])
            # # print("{} Afterr: {}".format(offset, data[offset:offset+20]))
            offset += 20
        offset = self.offset + 0x250
        # print("===========> Packing texture matrix at {}".format(offset))
        # texture matrix - ignores the actual matrix part
        for layer in self.layers:
            pack_into("> 4B", data, offset, layer.scn0CameraRef, layer.scn0LightRef, layer.mapMode, layer.enableIdentityMatrix)
            offset += 52
        # Light channel
        file.offset = self.offset + 0x3f0
        # print("===========> Packing lightchannels at {}:\n{}".format(file.offset, data[file.offset:file.offset+20]))
        self.lightChannels[0].pack(file)
        # print("{}".format(data[file.offset:file.offset+20]))
        file.offset += 20
        # print("===========> Packing lightchannels at {}:\n{}".format(file.offset, data[file.offset:file.offset+20]))
        self.lightChannels[1].pack(file)
        # print("{}".format(data[file.offset:file.offset+20]))

    def getMdlOffset(self):
        return self.mdl0Offset + self.offset


    def unpack(self, file):
        self.offset = file.offset
        matData = file.read(Struct("> 5I 4B I 4B 4B 4B"), 40) #up to 0x20
        print("\t{} Name: {}, index: {}".format(self.offset, self.name, matData[3]))
        print("Flags: {}, texgens: {}, lights: {}, shaderstages: {}, indirectStages: {}".format(matData[4], matData[5], matData[6], matData[7], matData[8]))
        print("Cull: {}, CompareBeforeTexture: {}, Lightset: {}, Fogset: {}".format(matData[9], matData[10], matData[11], matData[12]))
        self.length = matData[0]
        self.mdl0Offset = matData[1]
        self.nameOffset = matData[2]
        self.id = matData[3]
        self.xlu = matData[4] >> 31 & 1
        self.numLayers = matData[5]
        self.numLights = matData[6]
        self.shaderStages = matData[7]
        self.indirectStages = matData[8]
        # self.flags = ?
        self.cullmode = matData[9]
        self.compareBeforeTexture = matData[10]
        self.lightset = matData[11]
        self.fogset = matData[12]
        oset = file.offset
        matData = file.read(Struct("> 6I"), 24)
        self.shaderOffset = matData[0]
        self.numTextures = matData[1] # is this ever different from numlayers?
        self.layerOffset = matData[2]
        self.furDataOffset = matData[3]
        self.displayListOffset0 = matData[4]
        self.displayListOffset1 = matData[5]
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
        self.modeOffset = file.offset
        oset = file.offset
        mode = file.read(Struct("32B"), 32)
        # print("\t{} MODE: {}".format(oset, mode))
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
        self.constAlpha = mode[24]
        # print("Const Alpha is {} {}".format(mode[23], mode[24]))
        oset = file.offset
        tev = file.read(Struct("128B"), 128)
        # A tev[2-3] R tev[4] G tev[7-8] B tev[9]
        # G and B are repeated 3 times for some reason
        j = 2
        for i in range(3):
            self.colors.append((tev[2 + j], (tev[5 + j] << 4) | (tev[6 + j] >> 4), tev[7 + j], (tev[j] << 4) | (tev[1 + j] >> 4)))
            j += 20
            # print("Color: {}".format(self.colors[i]))
        j += 4
        for i in range(4):
            self.constantColors.append((tev[2 + j], ((tev[5 + j] & 0xf) << 4) | (tev[6 + j] >> 4), tev[7 + j], ((tev[j] & 0xf) << 4) | (tev[1 + j] >> 4)))
            j+=10
            # print("Color: {}".format(self.constantColors[i]))
        # print("\t{} Tev: {}".format(oset, tev))
        oset = file.offset
        shaderTex = file.read(Struct("64B"), 64)
        # print("\t{} TexTransform: {}".format(oset, shaderTex))
        oset = file.offset
        xfFlags = file.read(Struct("160B"), 160)
        # print("\t{} Matrices: {}".format(oset, xfFlags))
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
            # print("light {} source {} coordinates {} project {} inputform {} type {} normalize {}".format(layer.embossLight, layer.embossSource, layer.coordinates, layer.projection, layer.inputform, layer.type, layer.normalize))
            j += 18

        # for i in range(8):"
        #     shader = file.read(Struct("48B"), 48)
        #     # print(shader)

        file.offset = self.offset + 0x1a8
        matData = file.read(Struct("< 4B I"), 8)
        layerIndex = 0
        for i in range(3, -1, -1): # read it backwards
            # # print("Layer Flags: {}".format(flags))
            layer = self.getLayer(layerIndex)
            if layer:
                flags = matData[i]
                layer.enable = flags & 1
                layer.scaleFixed = (flags & 2) >> 1
                layer.rotationFixed = (flags & 4) >> 2
                layer.translationFixed = (flags & 8) >> 3
            layerIndex += 1
            layer = self.getLayer(layerIndex)
            if layer:
                flags = matData[i] >> 4
                layer.enable = flags & 1
                layer.scaleFixed = (flags & 2) >> 1
                layer.rotationFixed = (flags & 4) >> 2
                layer.translationFixed = (flags & 8) >> 3
            layerIndex += 1
        self.textureMatrixMode = matData[4]
        # # print("Mat Flags {}".format(matData))
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
                # print("Name: {}, Scale: {}, Rotation: {}, translation: {}".format(layer.name, layer.scale, layer.rotation, layer.translation))
        # Texture Matrix
        for i in range(8):
            layer = self.getLayer(i)
            if layer:
                matData = file.read(Struct("> 4B 12f"), 52)
                layer.scn0CameraRef = matData[0]
                layer.scn0LightRef = matData[1]
                layer.mapMode = matData[2]
                layer.enableIdentityMatrix = matData[3]
                # layer.textureMatrix = matData[4:]
                # # print("Texture matrix: {}".format(layer.textureMatrix))
            else:
                file.offset += 52
        # Lighting channels
        self.lightChannels.append(LightChannel(file))
        self.lightChannels.append(LightChannel(file))


    def isChanged(self):
        if self.isModified:
            return True
        for layer in self.layers:
            if layer.isModified:
                return True
        return False


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
            self.isModified = True
        if not self.xlu or self.compareBeforeTexture:
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

    def setTransparentStr(self, str):
        val = validBool(str)
        self.setTransparent() if val else self.setOpaque()

    def setShaderOffset(self, offset):
        self.shaderOffset = offset - self.offset

    def setShaderColorStr(self, str):
        const = "constantcolor"
        non = "color"
        isConstant = False
        if const in str:
            isConstant = True
            splitIndex = len(const)
        elif non in str:
            splitIndex = len(non)
        else:
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        index = int(str[splitIndex])
        if not 0 <= index <= 3 or (not isConstant) and index == 3:
            # print("Color Selection index out of range (0-3)")
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        str = str[splitIndex+2:]
        colors = str.split(",")
        if len(colors) < 4:
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        intVals = []
        for x in colors:
            i = int(x)
            if not 0 <= i <= 255:
                raise ValueError(self.SHADERCOLOR_ERROR.format(str))
            intVals.append(i)
        list = self.constantColors if isConstant else self.colors
        list[index] = (intVals[0], intVals[1], intVals[2], intVals[3])
        self.isModified = True

    def setCullModeStr(self, cullstr):
        i = indexListItem(self.CULL_STRINGS, cullstr, self.cullmode)
        if i >= 0:
            self.cullmode = i
            self.isModified = True

    def setLightChannelStr(self, lcStr):
        if "vertex" in lcStr:
            enable = True
        elif "ambient" in lcStr:
            enable = False
        else:
            raise ValueError("Invalid Light channel " + lcStr + ", options are 'vertex' or 'ambient'")
        self.lightChannels[0].setVertex(enable)
        self.isModified = True

    def setLightsetStr(self, str):
        val = int(str)
        if val != -1:
            raise ValueError("Invalid lightset " + str + ", expected -1")
        if self.lightset != -1:
            self.lightset = -1
            self.isModified = True

    def setFogsetStr(self, str):
        val = int(str)
        if val != 0:
            raise ValueError("Invalid fogset " + str + ", expected 0")
        if self.fogset != 0:
            self.fogset = 0
            self.isModified = True

    def setConstantAlphaStr(self, str):
        if "disable" in str:
            val = -1
        elif "enable" in str:
            val = -2
        else:
            val = int(str)
        if val > 255 or val < -2:
            raise ValueError("Invalid alpha " + str + ", expected 0-255|enable|disable")
        if val == -1:
            if not self.constAlphaEnable:
                self.constAlphaEnable = False
                self.isModified = True
        elif val == -2:
            if self.constAlphaEnable:
                self.constAlphaEnable = True
                self.isModified = True
        else:
            if not self.constAlphaEnable  or self.constAlpha != val:
                self.constAlphaEnable = True
                self.constAlpha = val
                self.isModified = True

    def setMatrixModeStr(self, str):
        if "maya" in str:
            if self.textureMatrixMode != self.MATRIXMODE_MAYA:
                self.textureMatrixMode = self.MATRIXMODE_MAYA
                self.isModified = True
        elif "xsi" in str:
            if self.textureMatrixMode != self.MATRIXMODE_XSI:
                self.textureMatrixMode = self.MATRIXMODE_XSI
                self.isModified = True
        elif "3dsmax" in str:
            if self.textureMatrixMode != self.MATRIXMODE_3DSMAX:
                self.textureMatrixMode = self.MATRIXMODE_3DSMAX
                self.isModified = True
        else:
            raise ValueError("Invalid Matrix Mode " + str + ", Expected Maya|XSI|3DSMax")

    def setRef0Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref0 must be 0-255")
        if not self.ref0 == val:
            self.ref0 = val
            self.isModified = True

    def setRef1Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref1 must be 0-255")
        if not self.ref1 == val:
            self.ref1 = val
            self.isModified = True

    def setComp0Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp0)
        if i >= 0:
            self.comp0 = self.COMP_STRINGS[i]
            self.isModified = True

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp1)
        if i >= 0:
            self.comp1 = self.COMP_STRINGS[i]
            self.isModified = True

    def setCompareBeforeTexStr(self, str):
        val = validBool(str)
        if val != self.compareBeforeTexture:
            self.compareBeforeTexture = val
            self.isModified = True

    def setBlendStr(self, str):
        val = validBool(str)
        if val != self.enableBlend:
            self.enableBlend = val
            self.isModified = True

    def setBlendSrcStr(self, str):
        i = indexListItem(self.BLFACTOR_STRINGS, str, self.srcFactor)
        if i >= 0:
            self.srcFactor = i
            self.isModified = True

    def setBlendDestStr(self, str):
        i = indexListItem(self.BLFACTOR_STRINGS, str, self.dstFactor)
        if i >= 0:
            self.dstFactor = i
            self.isModified = True

    def setBlendLogicStr(self, str):
        i = indexListItem(self.BLLOGIC_STRINGS, str, self.blendlogic)
        if i >= 0:
            self.blendlogic = i
            self.isModified = True

    def setEnableDepthTestStr(self, str):
        val = validBool(str)
        if val != self.enableDepthTest:
            self.enableDepthTest = val
            self.isModified = True

    def setEnableDepthUpdateStr(self, str):
        val = validBool(str)
        if val != self.enableDepthUpdate:
            self.enableDepthUpdate = val
            self.isModified = True

    def setDepthFunctionStr(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.depthFunction)
        if i >= 0:
            self.depthFunction = self.COMP_STRINGS[i]
            self.isModified = True

    def setDrawPriorityStr(self, str):
        i = int(str)
        if not 0 <= i <= 255:
            raise ValueError("Invalid setting '" + str + "', Draw priority must be 0-255")
        if i != self.drawPriority:
            self.drawPriority = i
            self.isModified = True

    def info(self, command):
        print("Mat {}: {}\tlayers:{} xlu:{} cull:{} blend:{} light:{}".format(self.id, self.name,
        self.numLayers, self.xlu, self.CULL_STRINGS[self.cullmode], self.enableBlend,
        self.lightChannels[0].getLight()))


class Layer:
    SETTINGS = [
    "scale", "rotation", "translation", "scn0cameraref",
    "scn0lightref", "mapmode", "uwrap", "vwrap",
    "minfilter", "magfilter", "lodbias", "anisotrophy",
    "clampbias", "texelinterpolate", "projection", "inputform",
    "type", "coordinates", "embosssource", "embosslight",
    "normalize"]
    WRAP=["clamp", "repeat", "mirror"]
    FILTER = ["nearest", "linear", "nearest_mipmap_nearest", "linear_mipmap_nearest", "nearest_mipmap_linear", "linear_mipmap_linear"]
    ANISOTROPHY = ["one", "two", "four"]
    MAPMODE = ["texcoord", "envcamera", "projection", "envlight", "envspec"]
    PROJECTION = ["st", "stq"]
    INPUTFORM = ["ab11", "abc1"]
    TYPE = ["regular", "embossmap", "color0", "color1"]
    COORDINATES = ["geometry", "normals", "colors", "binormalst", "binormalsb",
    "texcoord0", "texcoord1", "texcoord2", "texcoord3", "texcoord4", "texcoord5", "texcoord6", "texcoord7"]

    def __init__(self, file):
        offset = file.offset
        layer = file.read(Struct("> 10I f I 4B"), 52)
        # # print("Layer: {}".format(layer))
        name = file.unpack_name(layer[0] + offset)
        self.nameOffset = layer[0]
        self.name = name.decode()
        self.isModified = False
        self.palettenameOffset = layer[1]
        self.textureDataOffset = layer[2]
        self.palleteOffset = layer[3]
        self.texDataID = layer[4]
        self.palleteDataID = layer[5]
        self.uwrap = layer[6]
        self.vwrap = layer[7]
        self.minFilter = layer[8]
        self.magFilter = layer[9]
        self.LODBias = layer[10]
        self.maxAnisotrophy = layer[11]
        self.clampBias = layer[12]
        self.texelInterpolate = layer[13]

    def pack_texRef(self, file):
        pack_into("> 10I f I 2B", file.file, file.offset, self.nameOffset, self.palettenameOffset,
        self.textureDataOffset, self.palleteOffset, self.texDataID, self.palleteDataID,
        self.uwrap, self.vwrap, self.minFilter, self.magFilter, self.LODBias, self.maxAnisotrophy,
        self.clampBias, self.texelInterpolate)

    def pack_xfFlags(self, file): # aka texture matrices
        pack_into("> 4B", file.file, file.offset, self.embossLight >> 8, self.embossLight >> 1,
        self.embossLight << 7 & 0x80 | self.embossSource << 4 & 0x70 | self.coordinates >> 1 & 7,
        (self.coordinates & 1) << 7 | (self.projection & 1) << 1 | (self.inputform & 1) << 2 | (self.type & 3) << 4)
        pack_into("> B", file.file, file.offset + 11, self.normalize)

    def setScaleStr(self, str):
        values = parseValStr(str)
        if len(values) < 2:
            raise ValueError("Scale requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.scale[0] != i1 or self.scale[1] != i2:
            if i1 != 1 or i2 != 1:
                self.scaleFixed = False
            else:
                self.scaleFixed = True
            self.scale = (i1, i2)
            self.isModified = True

    def setRotationStr(self, str):
        f = float(str)
        if f != self.rotation:
            self.rotation = f
            self.rotationFixed = False if self.rotation == 0 else True
            self.isModified = True

    def setTranslationStr(self, str):
        values = parseValStr(str)
        if len(values) < 2:
            raise ValueError("Translation requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.translation[0] != i1 or self.translation[1] != i2:
            self.translation = (i1, i2)
            self.translationFixed = True if i1 == 1 and i2 == 1 else False
            self.isModified = True

    def setCameraRefStr(self, str):
        i = int(str)
        if i != -1 and i != 0:
            raise ValueError("Expected -1 or 0 for camera reference")
        if self.scn0CameraRef != i:
            self.scn0CameraRef = i
            self.isModified = True

    def setLightRefStr(self, str):
        i = int(str)
        if i != -1:
            raise ValueError("Expected -1 for light reference")
        if self.scn0LightRef != i:
            self.scn0LightRef = i
            self.isModified = True

    def setMapmodeStr(self, str):
        i = indexListItem(self.MAPMODE, str, self.mapMode)
        if i >= 0:
            self.mapMode = i
            self.isModified = True

    def setUWrapStr(self, str):
        i = indexListItem(self.WRAP, str, self.uwrap)
        if i >= 0:
            self.uwrap = i
            self.isModified = True

    def setVWrapStr(self, str):
        i = indexListItem(self.WRAP, str, self.vrap)
        if i >= 0:
            self.vrap = i
            self.isModified = True


    def setMinFilterStr(self, str):
        i = indexListItem(self.FILTER, str, self.minFilter)
        if i >= 0:
            self.minFilter = i
            self.isModified = True


    def setMagFilterStr(self, str):
        i = indexListItem(self.FILTER, str, self.magFilter)
        if i > 1:
            raise ValueError("MagFilter out of range (0-1)")
        elif i >= 0:
            self.minFilter = i
            self.isModified = True

    def setLodBiasStr(self, str):
        f = float(str)
        if f != self.LODBias:
            self.LODBias = f
            self.isModified = True

    def setAnisotrophyStr(self, str):
        invalidI = False
        try:
            i = int(str)
            if i != 1 and i != 2 and i != 4:
                invalidI = True
            else:
                i -= 1
                if i > 2:
                    i = 2
        except ValueError:
            i = indexListItem(ANISOTROPHY, str, self.maxAnisotrophy)
        if invalidI:
            raise ValueError("Invalid: '" + str + "', Anisotrophy expects 1|2|4")
        if i >= 0 and i != self.maxAnisotrophy:
            self.maxAnisotrophy = i
            self.isModified = True

    def setClampBiasStr(self, str):
        val = validBool(str)
        if val != self.clampBias:
            self.clampBias = val
            self.isModified = True

    def setTexelInterpolateStr(self, str):
        val = validBool(str)
        if val != self.texelInterpolate:
            self.texelInterpolate = val
            self.isModified = True

    def setProjectionStr(self, str):
        i = indexListItem(self.PROJECTION, str, self.projection)
        if i >= 0:
            self.projection = i
            self.isModified = True

    def setInputFormStr(self, str):
        i = indexListItem(self.INPUTFORM, str, self.inputform)
        if i >= 0:
            self.inputform = i
            self.isModified = True
    def setTypeStr(self, str):
        i = indexListItem(self.TYPE, str, self.type)
        if i >= 0:
            self.type = i
            self.isModified = True

    def setCoordinatesStr(self, str):
        i = indexListItem(self.COORDINATES, str, self.coordinates)
        if i >= 0:
            self.coordinates = i
            self.isModified = True

    def setEmbossSourceStr(self, str):
        i = int(str)
        if not 0 <= i <= 7:
            raise ValueError("Value '" + str + "' out of range for emboss source")
        if self.embossSource != i:
            self.embossSource = i
            self.isModified = True

    def setEmbossLightStr(self, str):
        i = int(str)
        if not 0 <= i <= 255:
            raise ValueError("Value '" + str + "' out of range for emboss light")
        if self.embossLight != i:
            self.embossLight = i
            self.isModified = True

    def setNormalizeStr(self, str):
        val = validBool(str)
        if val != self.normalize:
            self.normalize = val
            self.isModified = True

    def info(self, command):
        print("L {}:\tScale:{} Rot:{} Trans:{} UWrap:{} VWrap:{} MinFilter:{}".format(self.name,
        self.scale, self.rotation, self.translation, self.WRAP[self.uwrap], self.WRAP[self.vwrap], self.FILTER[self.minFilter]))


class Shader:
    def __init__(self, file):
        self.offset = file.offset
        data = file.read(Struct("> 3I 4B 8B 2I"), 0x20)
        self.length = data[0]
        self.mdl0Offset = data[1]
        self.id = data[2]
        self.layercount = data[3]
        self.res = data[4:7]
        self.references = data[7:15]
        print("\t{}\tShader {} length {} layercount {}".format(self.offset, self.id, self.length, self.layercount))
        self.swapTable = file.read(Struct("> 80B"), 0x50)
        print("Swap table: {}".format(self.swapTable))
        data = file.read(Struct("> 16B"), 16)
        print("Data is {}".format(data))
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
        print("Shader stage Data: {}".format(data))

class ShaderStage:
    def __init__(self, file):

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
    LIGHTS = ["ambient", "vertex"]
    def __init__(self, file):
        data = file.read(Struct("> I 16B"), 20)
        # print("Light Channel data {}".format(data))
        self.flags = data[0]
        self.materialColor = data[1:5]
        self.ambientColor = data[5:9]
        self.colorLightControl = data[9:13]
        self.alphaLightControl = data[13:17]

    def getLight(self):
        return self.LIGHTS[self.colorLightControl[3]]

    def isAmbient(self):
        return self.colorLightControl[3] == 0

    def isVertex(self):
        return self.colorLightControl[3] == 1


    def setVertex(self, vertexEnabled):
        self.colorLightControl[3] = 1 if vertexEnabled else 0
        self.alphaLightControl[3] = 1 if vertexEnabled else 0

    def pack(self, file):
        pack_into("> I 16B", file.file, file.offset,
        self.flags,
        self.materialColor[0], self.materialColor[1], self.materialColor[2], self.materialColor[3],
        self.ambientColor[0], self.ambientColor[1], self.ambientColor[2], self.ambientColor[3],
        self.colorLightControl[0],  self.colorLightControl[1], self.colorLightControl[2], self.colorLightControl[3],
        self.alphaLightControl[0], self.alphaLightControl[1], self.alphaLightControl[2], self.alphaLightControl[3])
