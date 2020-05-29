#!/usr/bin/Python
#---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
#---------------------------------------------------------------------
from struct import *

from matching import validBool, indexListItem, matches
from mdl0.layer import Layer
from mdl0.wiigraphics.matgx import MatGX

if __debug__:
    class OutAnalysis():
        def __init__(self):
            self.fname = "analysis.txt"
            self.file = open(self.fname, "a")
        def write(self, text):
            self.file.write(text + "\n")

    ANALYSIS = OutAnalysis()

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
    COMP_GREATEROREQUAL = 6
    COMP_LESSOREQUAL = 3
    COMP_ALWAYS = 7
    # Blend factor
    BLLOGIC_STRINGS = ("clear", "and", "reverseand", "copy",
    "inverseand", "nooperation", "exclusiveor", "or", "notor", "equivalent", "inverse",
    "reverseor", "inversecopy", "inverseor", "notand", "set")
    BLFACTOR_STRINGS = ("zero", "one", "sourcecolor", "inversesourcecolor",
     "sourcealpha", "inversesourcealpha", "destinationalpha", "inversedestinationalpha")
    # Matrix mode
    MATRIXMODE = ("maya", "xsi", "3dsmax")

    SHADERCOLOR_ERROR = "Invalid color '{}', Expected [constant]color<i>=<r>,<g>,<b>,<a>"


    def __init__(self, name, parent=None):
        self.parent = parent
        self.isModified = False
        self.name = name
        self.layers = []
        self.lightChannels = []
        self.shader = None      # to be hooked up
        self.drawlist = None    # to be hooked up
        self.srt0 = None        # to be hooked up
        self.matGX = MatGX()

    def __str__(self):
        # print("Cull mode is {}".format(self.cullmode))
        return  "Mt{} {}: xlu {} layers {} culling {} blend {}".format(self.id, self.name,
        self.xlu, len(self.layers), self.CULL_STRINGS[self.cullmode], self.getBlend())

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
        return self.matGX.alphafunction.getRef0()

    def getRef1(self):
        return self.matGX.alphafunction.getRef1()

    def getComp0(self):
        return self.COMP_STRINGS[self.matGX.alphafunction.getComp0()]

    def getComp1(self):
        return self.COMP_STRINGS[self.matGX.alphafunction.getComp1()]

    def getCompareBeforeTexture(self):
        return self.compareBeforeTexture

    def getBlend(self):
        return self.matGX.blendmode.isEnabled()

    def getBlendSrc(self):
        return self.BLFACTOR_STRINGS[self.matGX.blendmode.getSrcFactor()]

    def getBlendLogic(self):
        return self.BLLOGIC_STRINGS[self.matGX.blendmode.getBlendLogic()]

    def getBlendDest(self):
        return self.BLFACTOR_STRINGS[self.matGX.blendmode.getDstFactor()]

    def getConstantAlpha(self):
        ca = self.matGX.constantalpha
        if not ca.isEnabled():
            return -1
        return ca.get()

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
        for i in range(3):
            str += "Color{}: {}\t".format(i, self.matGX.tevRegs[i].getColor())
        str += "\n\t"
        for i in range(4):
            str += "Const{}: {}\t".format(i, self.matGX.cctevRegs[i].getColor())
        return str

    def  getMatrixMode(self):
        return self.MATRIXMODE[self.textureMatrixMode]

    def getEnableDepthTest(self):
        return self.matGX.zmode.getDepthTest()

    def getEnableDepthUpdate(self):
        return self.matGX.zmode.getDepthUpdate()

    def getDepthFunction(self):
        return self.COMP_STRINGS[self.matGX.zmode.getDepthFunction()]

    def getDrawPriority(self):
        return self.drawPriority

    def getLayer(self, i):
        if i < len(self.layers):
            return self.layers[i]
        return None

    # Get Functions
    GET_SETTING = ( getXlu, getXlu, getRef0, getRef1, getComp0, getComp1, getCompareBeforeTexture,
    getBlend, getBlendSrc, getBlendLogic, getBlendDest, getConstantAlpha, getCullMode, getShader,
    getShaderColor, getLightChannel, getLightset, getFogset, getMatrixMode, getEnableDepthTest,
    getEnableDepthUpdate, getDepthFunction, getDrawPriority)

    def __getitem__(self, key):
        for i in range(self.NUM_SETTINGS):
            if key == self.SETTINGS[i]:
                return self.SET_SETTING[i]


# ---------------------------------------------------------------------------
#   SETTERS
# ---------------------------------------------------------------------------

    def __setitem__(self, key, value):
        for i in range(self.NUM_SETTINGS):
            if key == self.SETTINGS[i]:
                func = self.SET_SETTING[i]
                return func(value)

    def setTransparent(self):
        af = self.matGX.alphafunction
        if not af.getRef0() or af.getComp0() == self.COMP_ALWAYS:
            af.setRef0(128)
            af.setRef1(255)
            af.setComp0(self.COMP_GREATEROREQUAL)
            af.setComp1(self.COMP_LESSOREQUAL)
            self.isModified = True
        if not self.xlu or self.compareBeforeTexture:
            self.compareBeforeTexture = False
            self.xlu = True
            self.parent.drawXLU.insert(self.parent.drawOpa.pop(self.id))
            self.isModified = True

    def setOpaque(self):
        af = self.matGX.alphafunction
        if not self.xlu or af.getComp0() != self.COMP_ALWAYS or af.getComp1() != self.COMP_ALWAYS:
            af.setRef0(0)
            af.setRef1(0)
            af.setComp0(self.COMP_ALWAYS)
            af.setComp1(self.COMP_ALWAYS)
            self.compareBeforeTexture = True
            self.xlu = False
            self.parent.drawOpa.insert(self.parent.drawXLU.pop(self.id))
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
            raise ValueError("Shader '{}' does not exist in model '{}'!".format(shaderindex, self.parent.name))
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
        list = self.matGX.cctevRegs if isConstant else self.matGX.tevRegs
        list[index].setColor(intVals)
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
        ca = self.matGX.constantalpha
        enabled = ca.isEnabled()
        if val == -1:
            if enabled:
                ca.setEnabled(False)
                self.isModified = True
        elif val == -2:
            if not enabled:
                ca.setEnabled(True)
                self.isModified = True
        else:
            if not enabled  or ca.get() != val:
                ca.setEnabled(True)
                ca.set(val)
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
        af = self.matGX.alphafunction
        if af.getRef0() != val:
            af.setRef0(val)
            self.isModified = True

    def setRef1Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref1 must be 0-255")
        af = self.matGX.alphafunction
        if af.getRef1() != val:
            af.setRef1(val)
            self.isModified = True

    def setComp0Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp0)
        if i >= 0:
            self.matGX.alphafunction.setComp0(i)
            self.isModified = True

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp1)
        if i >= 0:
            self.matGX.alphafunction.setComp1(i)
            self.isModified = True

    def setCompareBeforeTexStr(self, str):
        val = validBool(str)
        if val != self.compareBeforeTexture:
            self.compareBeforeTexture = val
            self.isModified = True

    def setBlendStr(self, str):
        val = validBool(str)
        b = self.matGX.blendmode
        if val != b.isEnabled():
            b.setEnabled(val)
            self.isModified = True

    def setBlendSrcStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLFACTOR_STRINGS, str, b.getSrcFactor())
        if i >= 0:
            b.setSrcFactor(i)
            self.isModified = True

    def setBlendDestStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLFACTOR_STRINGS, str, b.getDstFactor())
        if i >= 0:
            b.setDstFactor(i)
            self.isModified = True

    def setBlendLogicStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLLOGIC_STRINGS, str, b.getBlendLogic())
        if i >= 0:
            b.setBlendLogic(i)
            self.isModified = True

    def setEnableDepthTestStr(self, str):
        val = validBool(str)
        d = self.matGX.zmode
        if val != d.getDepthTest():
            d.setDepthTest(val)
            self.isModified = True

    def setEnableDepthUpdateStr(self, str):
        val = validBool(str)
        d = self.matGX.zmode
        if val != d.getDepthUpdate():
            d.setDepthUpdate(val)
            self.isModified = True

    def setDepthFunctionStr(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.depthFunction)
        d = self.matGX.zmode
        if i >= 0:
            d.setDepthFunction(i)
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

    def removeLayer(self, name):
        ''' Removes layer from material by name '''
        for i, x in enumerate(self.layers):
            if x.name == name:
                del self.layers[i]
                break

    def addLayer(self, name):
        ''' Creates and returns new layer '''
        l = Layer(len(self.layers), name, self)
        self.layers.append(l)
        return l

# -----------------------------------------------------------------------------
# PACKING
# -----------------------------------------------------------------------------
    def pack(self, binfile):
        ''' Packs the material '''
        if not self.isChanged():
            return
        binfile.start()
        self.offset = binfile.offset    # for backtracking offsets like shaders
        binfile.markLen()
        binfile.write("I", binfile.getOuterOffset())
        binfile.storeNameRef()
        binfile.write("2I4BI3B", self.id, self.xlu << 31, len(self.layers), len(self.lightChannels),
                      self.shaderStages, self.indirectStages, self.cullmode,
                      self.compareBeforeTexture, self.lightset, self.fogset)
        # print("===========> Packing mat flags at {}:\n{}".format(self.offset, data[self.offset:31 + self.offset]))
        binfile.write("BI4B", 0, 0, [0xff] * 4) # padding, indirect method, light normal map
        binfile.mark()  # shader offset, to be filled
        binfile.write("I", len(self.layers))
        binfile.mark()  # layer offset
        binfile.write("I", 0)   # fur not supported
        if self.version >= 10:
            binfile.advance(4)
            binfile.mark()  # matgx
        else:
            binfile.mark()  #matgx
            binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        # layer flags
        x = layerI = bitshift = 0
        while layerI < len(self.layers):
            x |= self.layers[layerI].getFlagNibble << bitshift
            layerI += 1
            bitshift += 4
        binfile.write("2I", x, self.MATRIXMODE)
        binfile.createRef(1)
        for l in self.layers:
            l.pack_srt(binfile)
        for l in self.layers:
            l.pack_textureMatrix(binfile)
        for l in self.lightChannels:
            l.pack(binfile)
        for l in self.layers:
            l.pack(binfile)
        binfile.align()
        binfile.start() # MatGX section
        binfile.createRef(1)
        self.matGX.pack()
        offset = binfile.offset
        for l in self.layers:
            l.pack_xf(binfile)
        binfile.advance(0xa0 - (binfile.offset - offset))
        binfile.end()
        binfile.end()

    def unpackLayers(self, binfile, startLayerInfo, numlayers):
        ''' unpacks the material layers '''
        binfile.recall() # layers
        offset = binfile.offset
        for i in range(numlayers):
            binfile.start()
            scaleoffset = startLayerInfo + 8 + i * 20
            self.addLayer(binfile.unpack_name()).unpack(binfile, scaleoffset)
            print("Layer: {} ".format(self.layers[-1].name))
            binfile.end()
        # Layer Flags
        binfile.offset = startLayerInfo
        flags = binfile.read("4B", 4)
        layerIndex = 0
        i = 3
        for li in range(len(self.layers)):
            if li % 2 == 0:
                f = flags[i]
            else:
                f = flags[i] >> 4
                i -= 1
            self.layers[li].setLayerFlags(f)
        return offset

    def unpackLightChannels(self, binfile):
        ''' Unpacks the light channels '''
        for i in range(2):
            lc = LightChannel()
            self.lightChannels.append(lc)
            lc.unpack(binfile)


    def unpack(self, binfile):
        ''' Unpacks material '''
        binfile.start()
        offset = binfile.offset
        l, mdOff = binfile.read("Ii", 8)
        binfile.advance(4)
        self.id, xluFlags, ntexgens, nlights, \
            self.shaderStages, self.indirectStages, \
            self.cullmode, self.compareBeforeTexture, \
            self.lightset, self.fogset, pad  = binfile.read("2I2B2BI4B", 20)
        self.xlu = xluFlags >> 31 & 1
        if __debug__:
            print("id {} xlu {} layers{} lights {}".format(self.id, xluFlags, ntexgens, nlights))
        binfile.advance(8)
        self.shaderOffset, nlayers = binfile.read("2I", 8)
        self.shaderOffset += binfile.beginOffset
        binfile.store() #  layer offset
        if self.parent.version >= 10:
            binfile.advance(8)
            bo = binfile.offset
            [dpo] = binfile.readOffset("I", binfile.offset)
            binfile.store() # store matgx offset
        else:
            binfile.advance(4)
            binfile.store() # store matgx offset
            binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        startlayerInfo = binfile.offset
        offset = self.unpackLayers(binfile, startlayerInfo, nlayers)
        self.textureMatrixMode = binfile.read("I", 4)
        binfile.advance(576)
        self.unpackLightChannels(binfile)
        binfile.recall()
        binfile.start() # Mat wii graphics
        self.matGX.unpack(binfile)
        for layer in self.layers:
            layer.unpackXF(binfile)

        binfile.end()
        binfile.end()


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
    def __init__(self, enabled = True):
        self.flags =  0xff # todo

    def getLight(self):
        return self.LIGHTS[(self.colorLightControl[3] & 1)]

    def isRegister(self):
        return self.colorLightControl[3] == 0

    def isVertex(self):
        return self.colorLightControl[3] == 1


    def setVertex(self, vertexEnabled):
        self.colorLightControl[3] = self.colorLightControl[3] & 1 if vertexEnabled else self.colorLightControl[3] & 2
        self.alphaLightControl[3] = self.alphaLightControl[3] & 1 if vertexEnabled else self.alphaLightControl[3] & 2

    def unpack(self, binfile):
        data = binfile.read("I16B", 20)
        # print("Light Channel data {}".format(data))
        self.flags = data[0]
        self.materialColor = data[1:5]
        self.ambientColor = data[5:9]
        self.colorLightControl = data[9:13]
        self.alphaLightControl = data[13:17]

    def pack(self, binfile):
        pack_into("I16B", binfile, self.materialColor, self.ambientColor,
                  self.colorLightControl, self.alphaLightControl)
