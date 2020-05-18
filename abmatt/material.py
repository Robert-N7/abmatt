#!/usr/bin/Python
#---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
#---------------------------------------------------------------------
import unpack
from struct import *
import re
from layer import *
BOOLABLE = ["False", "True"]

class Material:
# -----------------------------------------------------------------------
#   CONSTANTS
# -----------------------------------------------------------------------
    NUM_SETTINGS = 23
    SETTINGS = ("xlu", "transparent", "ref0", "ref1", #4
    "comp0", "comp1", "comparebeforetexture", "blend", #8
    "blendsrc", "blendlogic", "blenddest", "constantalpha",
    "cullmode", "shader", "shadercolor", "lightchannel", #16
    "lightset", "fogset", "matrixmode", "enabledepthtest",
    "enabledepthupdate", "depthfunction", "drawpriority") #23

    # CULL MODES
    CULL_STRINGS = ("none", "outside", "inside", "all")
    # COMPARE
    COMP_STRINGS = ("never", "less", "equal", "lessorequal", "greater", "notequal", "greaterorequal", "always")
    # Blend factor
    BLLOGIC_STRINGS = ("clear", "and", "reverseand", "copy",
    "inverseand", "nooperation", "exclusiveor", "or", "notor", "equivalent", "inverse",
    "reverseor", "inversecopy", "inverseor", "notand", "set")
    BLFACTOR_STRINGS = ("zero", "one", "sourcecolor", "inversesourcecolor",
     "sourcealpha", "inversesourcealpha", "destinationalpha", "inversedestinationalpha")
    # Matrix mode
    MATRIXMODE = ("maya", "xsi", "3dsmax")

    SHADERCOLOR_ERROR = "Invalid color '{}', Expected [constant]color<i>=<r>,<g>,<b>,<a>"


    def __init__(self, name, file, parent):
        self.parent = parent
        self.isModified = False
        self.name = name.decode()
        self.layers = []
        self.lightChannels = []
        self.colors = []
        self.constantColors = []
        self.shader = None
        self.unpack(file)

    def __str__(self):
        # print("Cull mode is {}".format(self.cullmode))
        return  "Mt{} {}: xlu {} layers {} culling {} blend {}".format(self.id, self.name,
        self.xlu, self.numLayers, self.CULL_STRINGS[self.cullmode], self.enableBlend)

# ==========================================================================
# Getters
# ==========================================================================
    def getKey(self, key):
        for i in range(len(self.SETTINGS)):
            if self.SETTINGS[i] == key:
                func = self.GET_SETTING[i]
                return func(self)
        return None

    def getXlu(self):
        return self.xlu

    def getRef0(self):
        return self.ref0

    def getRef1(self):
        return self.ref1

    def getComp0(self):
        return self.COMP_STRINGS[self.comp0]

    def getComp1(self):
        return self.COMP_STRINGS[self.comp1]

    def getCompareBeforeTexture(self):
        return self.compareBeforeTexture

    def getBlend(self):
        return self.enableBlend

    def getBlendSrc(self):
        return self.BLFACTOR_STRINGS[self.srcFactor]

    def getBlendLogic(self):
        return self.BLLOGIC_STRINGS[self.blendlogic]

    def getBlendDest(self):
        return self.BLFACTOR_STRINGS[self.dstFactor]

    def getConstantAlpha(self):
        if not self.constAlphaEnable:
            return -1
        return self.constAlpha

    def getCullMode(self):
        return self.CULL_STRINGS[self.cullmode]

    def getShader(self):
        if not self.shader:
            return -1
        return self.shader.id

    def getLightChannel(self):
        return self.lightChannels[0].getLight()

    def getLightset(self):
        return self.lightset

    def getFogset(self):
        return self.fogset

    def getShaderColor(self):
        str = ""
        for i in range(len(self.colors)):
            str += "Color{}: {}\t".format(i, self.colors[i])
        str += "\n\t"
        for i in range(len(self.constantColors)):
            str += "Const{}: {}\t".format(i, self.constantColors[i])
        return str

    def  getMatrixMode(self):
        return self.MATRIXMODE[self.textureMatrixMode]

    def getEnableDepthTest(self):
        return self.enableDepthTest

    def getEnableDepthUpdate(self):
        return self.enableDepthUpdate

    def getDepthFunction(self):
        return self.COMP_STRINGS[self.depthFunction]

    def getDrawPriority(self):
        return self.drawPriority

    def getMdlOffset(self):
        # print("Mdl0 offset {}\t my offset {} ".format(self.mdl0Offset, self.offset))
        return self.mdl0Offset + self.offset

    def getLayer(self, i):
        if i < len(self.layers):
            return self.layers[i]
        return None

    # Get Functions
    GET_SETTING = ( getXlu, getXlu, getRef0, getRef1, getComp0, getComp1, getCompareBeforeTexture,
    getBlend, getBlendSrc, getBlendLogic, getBlendDest, getConstantAlpha, getCullMode, getShader,
    getShaderColor, getLightChannel, getLightset, getFogset, getMatrixMode, getEnableDepthTest,
    getEnableDepthUpdate, getDepthFunction, getDrawPriority)

    def getSetter(self, key):
        for i in range(self.NUM_SETTINGS):
            if key == self.SETTINGS[i]:
                return self.SET_SETTING[i]


# ---------------------------------------------------------------------------
#   SETTERS
# ---------------------------------------------------------------------------

    def setKey(self, key, strvalue):
        for i in range(self.NUM_SETTINGS):
            if key == self.SETTINGS[i]:
                func = self.SET_SETTING[i]
                return func(strvalue)

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
            self.isMo
            dified = True

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

    def setShaderStr(self, str):
        try:
            shaderindex = int(str)
        except TypeError:
            print("Shader requires number: {} is not a number".format(str))
            return False
        shader = self.parent.getTev(shaderindex)
        if not shader:
            raise ValueError("Shader '{}' does not exist in model '{}'!".format(shaderindex, mdl.name))
        if self.setShader(shader):
            # update shader material entry
            self.parent.updateTevEntry(shader, self)


    def setShader(self, shader):
        if shader.offset !=  self.shaderOffset + self.offset:
            self.shaderOffset = shader.offset - self.offset
            self.shaderStages = shader.countDirectStages()
            self.indirectStages = shader.countIndirectStages()
            self.isModified = True
        self.shader = shader
        return self.isModified

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
            self.comp0 = i
            self.isModified = True

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp1)
        if i >= 0:
            self.comp1 = i
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

    # Set functions
    SET_SETTING= ( setTransparentStr, setTransparentStr, setRef0Str, setRef1Str,
    setComp0Str, setComp1Str, setCompareBeforeTexStr, setBlendStr, setBlendSrcStr,
    setBlendLogicStr, setBlendDestStr, setConstantAlphaStr, setCullModeStr,
    setShaderStr, setShaderColorStr, setLightChannelStr, setLightsetStr,
    setFogsetStr, setMatrixModeStr, setEnableDepthTestStr,
    setEnableDepthUpdateStr, setDepthFunctionStr, setDrawPriorityStr )

    def info(self, command, trace):
        trace += "->" + self.name
        shindex = self.shader.id if self.shader else -1
        if not command.materialname and matches(command.name, self.name):
            if command.key:
                val = self.getKey(command.key)
                if val is not None:
                    print("{}\t{}:{}".format(trace, command.key, val))
            else:
                print("{} {}\tlayers:{} xlu:{} cull:{} blend:{} light:{} shader:{}".format(trace, self.id,
                self.numLayers, self.xlu, self.CULL_STRINGS[self.cullmode], self.enableBlend,
                self.lightChannels[0].getLight(), shindex))
        # pass it along
        for layer in self.layers:
            layer.info(command, trace)

    def isChanged(self):
        if self.isModified:
            return True
        for layer in self.layers:
            if layer.isModified:
                return True
        return False


    def addLayer(self, layer):
        self.layers.append(layer)

# -----------------------------------------------------------------------------
# PACKING
# -----------------------------------------------------------------------------
    def pack(self, file):
        if not self.isChanged():
            return
        data = file.file
        args = (self.length, self.mdl0Offset, self.nameOffset,
        self.id, self.xlu << 31, self.numLayers, self.numLights, self.shaderStages,
        self.indirectStages, self.cullmode, self.compareBeforeTexture, self.lightset,
        self.fogset)
        # print("===========> Packing mat flags at {}:\n{}".format(self.offset, data[self.offset:31 + self.offset]))
        pack_into("> I i 3I 4B I 3B", data, self.offset, *args)
        offset = self.offset + 0x28
        pack_into("> 3I", data, offset, self.shaderOffset, self.numTextures, self.layerOffset)
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
        for i in range(3):
            color = self.colors[i]
            byte1 = color[3] >> 4 & 0x0f | data[offset] & 0xf0
            byte2 = color[3] << 4 & 0xf0 | data[offset + 1] & 0x0f
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
            self.layers[i].pack_texRef(file)
            file.offset += 52
        # layer flags
        offset = self.offset + 0x1a8
        layerIndex = 0
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
        # layer scale / Rotation
        for layer in self.layers:
            pack_into("> 5f", data, offset, layer.scale[0], layer.scale[1], layer.rotation,
            layer.translation[0], layer.translation[1])
            offset += 20
        offset = self.offset + 0x250
        # texture matrix - ignores the actual matrix part
        for layer in self.layers:
            pack_into("> 4B", data, offset, layer.scn0CameraRef, layer.scn0LightRef, layer.mapMode, layer.enableIdentityMatrix)
            offset += 52
        # Light channel
        file.offset = self.offset + 0x3f0
        self.lightChannels[0].pack(file)
        file.offset += 20
        self.lightChannels[1].pack(file)

    def unpack(self, file):
        self.offset = file.offset
        matData = file.read(Struct("> I i 3I 4B I 4B 4B 4B"), 40) #up to 0x20
        # print("\t{} Name: {}, index: {}".format(self.offset, self.name, matData[3]))
        # print("Flags: {}, texgens: {}, lights: {}, shaderstages: {}, indirectStages: {}".format(matData[4], matData[5], matData[6], matData[7], matData[8]))
        # print("Cull: {}, CompareBeforeTexture: {}, Lightset: {}, Fogset: {}".format(matData[9], matData[10], matData[11], matData[12]))
        self.length = matData[0]
        self.mdl0Offset = matData[1]
        self.nameOffset = matData[2]
        self.id = matData[3]
        self.xlu = matData[4] >> 31 & 1
        self.numLayers = matData[5]
        self.numLights = matData[6]
        self.shaderStages = matData[7]
        self.indirectStages = matData[8]
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
        # print("{} Shader Offset {}, numTextures {}, layer offset {}".format(oset, matData[0], matData[1], matData[2]))
        # Advance to layer offset
        file.offset = matData[2] + self.offset
        for i in range(matData[1]):
            ref = Layer(file, self)
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
        shaderTex = file.read(Struct("64B"), 64)
        xfFlags = file.read(Struct("160B"), 160)
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
            j += 18

        file.offset = self.offset + 0x1a8
        matData = file.read(Struct("< 4B I"), 8)
        layerIndex = 0
        for i in range(3, -1, -1): # read it backwards
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

# LIGHT CHANNEL ----------------------------------------------------
        # LC flags bits
        # 0	Material color enabled
        # 1	Material alpha enabled
        # 2	Ambient color enabled
        # 3	Ambient alpha enabled
        # 4	Raster color enabled
        # 5	Raster alpha enabled
# Light Controls
#   3rd byte 7 for activated, 4th 0-1 for register or vertex color
class LightChannel:
    LIGHTS = ["register", "vertex"]
    def __init__(self, file):
        data = file.read(Struct("> I 16B"), 20)
        # print("Light Channel data {}".format(data))
        self.flags = data[0]
        self.materialColor = data[1:5]
        self.ambientColor = data[5:9]
        self.colorLightControl = data[9:13]
        self.alphaLightControl = data[13:17]

    def getLight(self):
        return self.LIGHTS[(self.colorLightControl[3] & 1)]

    def isRegister(self):
        return self.colorLightControl[3] == 0

    def isVertex(self):
        return self.colorLightControl[3] == 1


    def setVertex(self, vertexEnabled):
        self.colorLightControl[3] = self.colorLightControl[3] & 1 if vertexEnabled else self.colorLightControl[3] & 2
        self.alphaLightControl[3] = self.alphaLightControl[3] & 1 if vertexEnabled else self.alphaLightControl[3] & 2

    def pack(self, file):
        pack_into("> I 16B", file.file, file.offset,
        self.flags,
        self.materialColor[0], self.materialColor[1], self.materialColor[2], self.materialColor[3],
        self.ambientColor[0], self.ambientColor[1], self.ambientColor[2], self.ambientColor[3],
        self.colorLightControl[0],  self.colorLightControl[1], self.colorLightControl[2], self.colorLightControl[3],
        self.alphaLightControl[0], self.alphaLightControl[1], self.alphaLightControl[2], self.alphaLightControl[3])
