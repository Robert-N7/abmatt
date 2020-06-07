#!/usr/bin/Python
# ---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
# ---------------------------------------------------------------------

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
    SETTINGS = ("xlu", "ref0", "ref1",
                "comp0", "comp1", "comparebeforetexture", "blend",
                "blendsrc", "blendlogic", "blenddest", "constantalpha",
                "cullmode", "shader", "shadercolor", "lightchannel",
                "lightset", "fogset", "matrixmode", "enabledepthtest",
                "enabledepthupdate", "depthfunction", "drawpriority", "drawxlu")

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
        self.shader = None  # to be hooked up
        self.drawlist = None  # to be hooked up
        self.srt0 = None  # to be hooked up
        self.matGX = MatGX()

    def __str__(self):
        return "Mt{} {}: xlu {} layers {} culling {} blend {}".format(self.id, self.name,
                                                                      self.xlu, len(self.layers),
                                                                      self.CULL_STRINGS[self.cullmode], self.getBlend())

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

    def getMatrixMode(self):
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

    def getDrawXLU(self):
        return self.parent.isMaterialDrawXLU(self.id)

    # Get Functions
    GET_SETTING = (getXlu, getRef0, getRef1, getComp0, getComp1, getCompareBeforeTexture,
                   getBlend, getBlendSrc, getBlendLogic, getBlendDest, getConstantAlpha, getCullMode, getShader,
                   getShaderColor, getLightChannel, getLightset, getFogset, getMatrixMode, getEnableDepthTest,
                   getEnableDepthUpdate, getDepthFunction, getDrawPriority, getDrawXLU)

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

    def setXluStr(self, str_value):
        val = validBool(str_value)
        if self.xlu != val:
            self.xlu = val

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
        if shader.offset != self.shaderOffset + self.offset:
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
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        str = str[splitIndex + 2:]
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
            if not enabled or ca.get() != val:
                ca.setEnabled(True)
                ca.set(val)
                self.isModified = True

    def setMatrixModeStr(self, str):
        if "maya" in str:
            if self.textureMatrixMode != 0:
                self.textureMatrixMode = 0
                self.isModified = True
        elif "xsi" in str:
            if self.textureMatrixMode != 1:
                self.textureMatrixMode = 1
                self.isModified = True
        elif "3dsmax" in str:
            if self.textureMatrixMode != 2:
                self.textureMatrixMode = 2
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
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.alphafunction.getComp0())
        if i >= 0:
            self.matGX.alphafunction.setComp0(i)
            self.isModified = True

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.alphafunction.getComp1())
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
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.zmode.getDepthFunction())
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

    def setDrawXLUStr(self, str_value):
        val = validBool(str_value)
        if val:
            self.parent.setMaterialDrawXLU(self.id)
        else:
            self.parent.setMaterialDrawOpa(self.id)

    # Set functions
    SET_SETTING = (setXluStr, setRef0Str, setRef1Str,
                   setComp0Str, setComp1Str, setCompareBeforeTexStr, setBlendStr, setBlendSrcStr,
                   setBlendLogicStr, setBlendDestStr, setConstantAlphaStr, setCullModeStr,
                   setShaderStr, setShaderColorStr, setLightChannelStr, setLightsetStr,
                   setFogsetStr, setMatrixModeStr, setEnableDepthTestStr,
                   setEnableDepthUpdateStr, setDepthFunctionStr, setDrawPriorityStr, setDrawXLUStr)

    def info(self, command, trace):
        trace = self.parent.getTrace() + "->" + self.name
        if matches(command.name, self.name):
            if command.key:
                val = self.getKey(command.key)
                if val is not None:
                    print("{}\t{}:{}".format(trace, command.key, val))
            else:
                print("{} {}\tlayers:{} xlu:{} cull:{} blend:{}".format(trace, self.id,
                                                                                 len(self.layers), self.xlu,
                                                                                 self.CULL_STRINGS[
                                                                                     self.cullmode],
                                                                                 self.getBlend()))

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
    def pack(self, binfile, texture_link_map):
        """ Packs the material """
        self.offset = binfile.start()
        binfile.markLen()
        binfile.write("i", binfile.getOuterOffset())
        binfile.storeNameRef(self.name)
        binfile.write("2I4BI3B", self.id, self.xlu << 31, len(self.layers), len(self.lightChannels),
                      self.shaderStages, self.indirectStages, self.cullmode,
                      self.compareBeforeTexture, self.lightset, self.fogset)
        binfile.write("BI4B", 0, 0, 0xff, 0xff, 0xff, 0xff)  # padding, indirect method, light normal map
        binfile.mark()  # shader offset, to be filled
        binfile.write("I", len(self.layers))
        binfile.mark()  # layer offset
        binfile.write("I", 0)  # fur not supported
        if self.parent.version >= 10:
            binfile.advance(4)
            binfile.mark()  # matgx
        else:
            binfile.mark()  # matgx
            binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        # layer flags
        x = layerI = bitshift = 0
        layers = self.layers
        empty_layer_count = 8 - len(layers)
        while layerI < len(self.layers):
            x |= layers[layerI].getFlagNibble() << bitshift
            layerI += 1
            bitshift += 4
        binfile.write("2I", x, self.textureMatrixMode)
        for l in layers:
            l.pack_srt(binfile)
        # fill in defaults
        Layer.pack_default_srt(binfile, empty_layer_count)
        for l in layers:
            l.pack_textureMatrix(binfile)
        Layer.pack_default_textureMatrix(binfile, empty_layer_count)
        assert (len(self.lightChannels) == 1)
        for l in self.lightChannels:
            l.pack(binfile)
        # pack 2nd lc padding
        LightChannel.pack_default(binfile)
        binfile.createRef(1)
        for l in layers:
            # Write Texture linker offsets
            start_offset = texture_link_map[l.name]
            tex_link_offsets = binfile.references[start_offset]
            binfile.writeOffset('i', tex_link_offsets.pop(0), self.offset - start_offset) # material offset
            binfile.writeOffset('i', tex_link_offsets.pop(0), binfile.offset - start_offset) # layer offset
            l.pack(binfile)

        binfile.createRef(1)
        binfile.start()  # MatGX section
        self.matGX.pack(binfile)
        offset = binfile.offset
        for l in layers:
            l.pack_xf(binfile)
        binfile.advance(0xa0 - (binfile.offset - offset))
        binfile.end()
        binfile.end()

    def unpackLayers(self, binfile, startLayerInfo, numlayers):
        """ unpacks the material layers """
        binfile.recall()  # layers
        offset = binfile.offset
        for i in range(numlayers):
            binfile.start()
            scale_offset = startLayerInfo + 8 + i * 20
            self.addLayer(binfile.unpack_name()).unpack(binfile, scale_offset)
            binfile.end()
        # Layer Flags
        binfile.offset = startLayerInfo
        flags = binfile.read("4B", 4)
        i = 3
        for li in range(len(self.layers)):
            if li % 2 == 0:
                f = flags[i]
            else:
                f = flags[i] >> 4
                i -= 1
            self.layers[li].setLayerFlags(f)
        # Texture matrix
        binfile.advance(164)
        for layer in self.layers:
            layer.unpack_textureMatrix(binfile)
        return offset

    def unpackLightChannels(self, binfile, nlights):
        ''' Unpacks the light channels '''
        for i in range(nlights):
            lc = LightChannel()
            self.lightChannels.append(lc)
            lc.unpack(binfile)

    def unpack(self, binfile):
        """ Unpacks material """
        binfile.start()
        l, mdOff = binfile.read("Ii", 8)
        binfile.advance(4)
        self.id, xluFlags, ntexgens, nlights, \
        self.shaderStages, self.indirectStages, \
        self.cullmode, self.compareBeforeTexture, \
        self.lightset, self.fogset, pad = binfile.read("2I2B2BI4B", 20)
        self.xlu = xluFlags >> 31 & 1
        assert(nlights == 0x1)
        binfile.advance(8)
        self.shaderOffset, nlayers = binfile.read("2i", 8)
        if nlayers != ntexgens:
            raise Exception('Number of layers {} is different than number texgens {}'.format(nlayers, ntexgens))
        self.shaderOffset += binfile.beginOffset
        binfile.store()  # layer offset
        if self.parent.version >= 10:
            binfile.advance(8)
            bo = binfile.offset
            [dpo] = binfile.readOffset("I", binfile.offset)
            binfile.store()  # store matgx offset
        else:
            binfile.advance(4)
            binfile.store()  # store matgx offset
            binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        startlayerInfo = binfile.offset
        [self.textureMatrixMode] = binfile.readOffset('I', binfile.offset + 4)
        self.unpackLayers(binfile, startlayerInfo, nlayers)
        binfile.offset = startlayerInfo + 584
        self.unpackLightChannels(binfile, nlights)
        binfile.recall()
        binfile.start()  # Mat wii graphics
        self.matGX.unpack(binfile)
        for layer in self.layers:
            layer.unpackXF(binfile)
        binfile.end()
        binfile.end()


# LIGHT CHANNEL ----------------------------------------------------
class LightChannel:

    def __init__(self):
        self.materialColorEnabled = False
        self.materialAlphaEnabled = False
        self.ambientColorEnabled = False
        self.ambientAlphaEnabled = False
        self.rasterColorEnabled = False
        self.rasterAlphaEnabled = False

    def __getitem__(self, item):
        is_color = True if "color" in item else False
        if "control" in item:
            return self.colorLightControl[item] if is_color else self.alphaLightControl[item]
        else:
            if "material" in item:
                return self.materialColorEnabled if is_color else self.materialAlphaEnabled
            elif "ambient" in item:
                return self.ambientColorEnabled if is_color else self.ambientAlphaEnabled
            elif "raster" in item:
                return self.rasterColorEnabled if is_color else self.rasterAlphaEnabled
        raise ValueError('Unknown key {} for light channel'.format(item))

    def __setitem__(self, key, value):
        is_color = True if "color" in key else False
        if "control" in key:
            if is_color:
                self.colorLightControl[key] = value
            else:
                self.alphaLightControl[key] = value
        else:
            val = validBool(value)
            if "material" in key:
                if is_color:
                    self.materialColorEnabled = val
                else:
                    self.materialAlphaEnabled = val
            elif "ambient" in key:
                if is_color:
                    self.ambientColorEnabled = val
                else:
                    self.ambientAlphaEnabled = val
            elif "raster" in key:
                if is_color:
                    self.rasterColorEnabled = val
                else:
                    self.rasterAlphaEnabled = val
        raise ValueError('Unknown key {} for light channel'.format(key))

    class LightChannelControl:
        LIGHT_SOURCE = ("register", "vertex")
        DIFFUSE_FUNCTION = ("disabled", "enabled", "clamped")
        ATTENUATION = ("specular", "spotlight")

        #   Channel control
        #         //0000 0000 0000 0000 0000 0000 0000 0001   Material Source (GXColorSrc)
        #         //0000 0000 0000 0000 0000 0000 0000 0010   Light Enabled
        #         //0000 0000 0000 0000 0000 0000 0011 1100   Light 0123
        #         //0000 0000 0000 0000 0000 0000 0100 0000   Ambient Source (GXColorSrc)
        #         //0000 0000 0000 0000 0000 0001 1000 0000   Diffuse Func
        #         //0000 0000 0000 0000 0000 0010 0000 0000   Attenuation Enable
        #         //0000 0000 0000 0000 0000 0100 0000 0000   Attenuation Function (0 = Specular)
        #         //0000 0000 0000 0000 0111 1000 0000 0000   Light 4567

        def __init__(self, flags):
            self.materialSourceVertex = flags & 1
            self.enabled = flags >> 1 & 1
            self.light0123 = flags >> 2 & 0xf
            self.ambientSourceVertex = flags >> 6 & 1
            self.diffuseFunction = flags >> 7 & 3
            self.attenuationEnabled = flags >> 9 & 1
            self.attenuationFunction = flags >> 10 & 1
            self.light4567 = flags >> 11 & 0xf

        def __getitem__(self, item):
            if 'material' in item:
                return self.LIGHT_SOURCE[self.materialSourceVertex]
            elif 'enabled' in item:
                return self.enabled
            elif 'ambient' in item:
                return self.LIGHT_SOURCE[self.ambientSourceVertex]
            elif 'diffuse' in item:
                return self.DIFFUSE_FUNCTION[self.diffuseFunction]
            elif 'attenuation' in item:
                return 'None' if not self.attenuationEnabled else self.ATTENUATION[self.attenuationFunction]
            else:
                raise ValueError('Unknown Light Control key {}'.format(item))

        def __setitem__(self, key, value):
            if 'material' in key:
                i = indexListItem(self.LIGHT_SOURCE, value, self.materialSourceVertex)
                if i > 0:
                    self.materialSourceVertex = i
            elif 'enabled' in key:
                val = validBool(value)
                self.enabled = val
            elif 'ambient' in key:
                i = indexListItem(self.LIGHT_SOURCE, value, self.ambientSourceVertex)
                if i >= 0:
                    self.ambientSourceVertex = i
            elif 'diffuse' in key:
                i = indexListItem(self.DIFFUSE_FUNCTION, value, self.diffuseFunction)
                if i >= 0:
                    self.diffuseFunction = i
            elif 'attenuation' in key:
                try:
                    i = indexListItem(self.ATTENUATION, value, self.attenuationFunction)
                    if i >= 0:
                        self.attenuationFunction = i
                    if not self.attenuationEnabled:
                        self.attenuationEnabled = True
                except ValueError:
                    val = validBool(value)
                    self.attenuationEnabled = val
            else:
                raise ValueError('Unknown Light Control key {}'.format(key))

        def getFlagsAsInt(self):
            return self.materialSourceVertex | self.enabled << 1 | self.light0123 << 2 | self.ambientSourceVertex << 6 \
                | self.diffuseFunction << 7 | self.attenuationEnabled << 9 | self.attenuationFunction << 10 \
                | self.light4567

    def unpack(self, binfile):
        data = binfile.read("I8B2I", 20)
        flags = data[0]
        self.materialColorEnabled = flags & 1
        self.materialAlphaEnabled = flags >> 1 & 1
        self.ambientColorEnabled = flags >> 2 & 1
        self.ambientAlphaEnabled = flags >> 3 & 1
        self.rasterColorEnabled = flags >> 4 & 1
        self.rasterAlphaEnabled = flags >> 5 & 1
        self.materialColor = data[1:5]
        self.ambientColor = data[5:9]
        self.colorLightControl = self.LightChannelControl(data[9])
        self.alphaLightControl = self.LightChannelControl(data[10])

    def pack(self, binfile):
        flags = self.materialColorEnabled | self.materialAlphaEnabled << 1 | self.ambientColorEnabled << 2 \
                | self.ambientAlphaEnabled << 3 | self.rasterColorEnabled << 4 | self.rasterAlphaEnabled << 5
        binfile.write("I8B2I", flags, *self.materialColor, *self.ambientColor,
                      self.colorLightControl.getFlagsAsInt(), self.alphaLightControl.getFlagsAsInt())

    @staticmethod
    def pack_default(binfile):
        binfile.write('5I', 0xf, 0xff, 0, 0, 0)