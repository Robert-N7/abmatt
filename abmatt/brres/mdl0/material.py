#!/usr/bin/Python
# ---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
# ---------------------------------------------------------------------
import re
from copy import deepcopy

from abmatt.brres.lib.matching import validBool, indexListItem, validInt, validFloat, splitKeyVal, MATCHING, parse_color
from abmatt.brres.lib.node import Clipable
from abmatt.brres.mdl0.layer import Layer
from abmatt.brres.mdl0.shader import Shader
from abmatt.brres.mdl0.wiigraphics.matgx import MatGX
from autofix import AutoFix


class Material(Clipable):
    # -----------------------------------------------------------------------
    #   CONSTANTS
    # -----------------------------------------------------------------------
    EXT = 'matl'
    SETTINGS = ("xlu", "ref0", "ref1",
                "comp0", "comp1", "comparebeforetexture", "blend",
                "blendsrc", "blendlogic", "blenddest", "constantalpha",
                "cullmode", "shadercolor", "lightchannel", "lightset",
                "fogset", "matrixmode", "enabledepthtest", "enabledepthupdate",
                "depthfunction", "drawpriority",
                "indirectmatrix", "name", "layercount")

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
    DEFAULT_COLOR = (200, 200, 200, 255)
    SHADERCOLOR_ERROR = "Invalid color '{}', Expected [constant]<i>:<r>,<g>,<b>,<a>"

    def __init__(self, name, parent=None, binfile=None):
        self.layers = []
        self.lightChannels = []
        self.shader = None  # to be hooked up
        self.srt0 = None  # to be hooked up
        self.pat0 = None  # to be hooked up
        self.polygons = []
        self.matGX = MatGX()
        super(Material, self).__init__(name, parent, binfile)

    def __deepcopy__(self, memodict={}):
        # don't copy references copied elsewhere
        srt0 = self.srt0
        self.srt0 = None
        pat0 = self.pat0
        self.pat0 = None
        shader = self.shader
        self.shader = None
        copy = super().__deepcopy__(memodict)
        self.srt0 = srt0
        self.pat0 = pat0
        self.shader = shader
        return copy

    def set_default_color(self):
        self.set_color(self.DEFAULT_COLOR)

    @staticmethod
    def get_unique_material(name, mdl):
        is_digit = False
        while True:
            mat = mdl.getMaterialByName(name)
            if not mat:
                return Material(name, mdl)
            if not is_digit and not name[-1].isdigit():
                name = name + '1'
                is_digit = True
            else:
                name = re.sub('\d+$', lambda x : str(int(x.group(0)) + 1), name)

    def begin(self):
        self.shaderStages = 0
        self.indirectStages = 0
        self.cullmode = 2
        self.compareBeforeTexture = True
        self.lightset = -1
        self.fogset = 0
        self.xlu = 0
        self.textureMatrixMode = 0
        self.lightChannels.append(LightChannel())
        self.shader = Shader(self.name, self.parent)
        self.parent.shaders[self.name] = self.shader
        self.shader.material = self

    def auto_detect_layer(self):
        if not self.layers:
            if self.name in self.get_texture_map():
                self.addLayer(self.name)

    def __str__(self):
        return "Mt{} {}: xlu {} layers {} culling {} blend {}".format(self.index, self.name,
                                                                      self.xlu, len(self.layers),
                                                                      self.CULL_STRINGS[self.cullmode], self.getBlend())

    # ==========================================================================
    # Getters
    # ==========================================================================
    def is_cull_none(self):
        return self.cullmode == 0

    def getKey(self, key):
        for i in range(len(self.SETTINGS)):
            if self.SETTINGS[i] == key:
                func = self.GET_SETTING[i]
                return func(self)
        return None

    def is_xlu(self):
        return self.xlu

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
        return self.shader

    def getLightChannel(self):
        return str(self.lightChannels[0])

    def getLightset(self):
        return self.lightset

    def getFogset(self):
        return self.fogset

    def getColor(self, i):
        return self.matGX.tevRegs[i].getColor()

    def getConstantColor(self, i):
        return self.matGX.cctevRegs[i].getColor()

    def getBrres(self):
        return self.parent.parent

    def getShaderColor(self):
        ret = ""
        for i in range(3):
            ret += "Color{}: {}\t".format(i, self.matGX.tevRegs[i].getColor())
        ret += "\n\t"
        for i in range(4):
            ret += "Const{}: {}\t".format(i, self.matGX.cctevRegs[i].getColor())
        return ret

    def getMatrixMode(self):
        return self.MATRIXMODE[self.textureMatrixMode]

    def getEnableDepthTest(self):
        return self.matGX.zmode.getDepthTest()

    def getEnableDepthUpdate(self):
        return self.matGX.zmode.getDepthUpdate()

    def getDepthFunction(self):
        return self.COMP_STRINGS[self.matGX.zmode.getDepthFunction()]

    def getDrawPriority(self):
        return {x.get_draw_priority() for x in self.polygons}

    def getName(self):
        return self.name

    def getLayerI(self, layer_index):
        if 0 <= layer_index < len(self.layers):
            return self.layers[layer_index]

    def getLayerByName(self, key):
        """Attempts to get layer(s) by string key"""
        layers = MATCHING.findAll(key, self.layers)
        if layers:
            return layers[0]

    def forceAdd(self, key):
        textures = self.parent.parent.getTextures(key)
        if textures:
            key = textures[0].name
        return self.addLayer(key)

    def getDrawXLU(self):
        return self.xlu
        # return self.parent.isMaterialDrawXlu(self.index)

    def getIndMatrix(self):
        ret = ''
        for i in range(3):
            matrix = self.matGX.getIndMatrix(i)
            ret += '\n\t{}: Scale {}, {}'.format(i, matrix.scale, matrix.matrix)
        return ret

    def getLayerCount(self):
        return len(self.layers)

    # Get Functions
    GET_SETTING = (getXlu, getRef0, getRef1, getComp0, getComp1, getCompareBeforeTexture,
                   getBlend, getBlendSrc, getBlendLogic, getBlendDest, getConstantAlpha, getCullMode,
                   getShaderColor, getLightChannel, getLightset, getFogset, getMatrixMode, getEnableDepthTest,
                   getEnableDepthUpdate, getDepthFunction, getDrawPriority, getIndMatrix, getName, getLayerCount)

    def get_str(self, key):
        for i in range(len(self.SETTINGS)):
            if key == self.SETTINGS[i]:
                return self.SET_SETTING[i]

    # ---------------------------------------------------------------------------
    #   SETTERS
    # ---------------------------------------------------------------------------

    def set_str(self, key, value):
        for i in range(len(self.SETTINGS)):
            if key == self.SETTINGS[i]:
                func = self.SET_SETTING[i]
                return func(self, value)

    def rename(self, value):
        if value == self.name:
            return True
        self.name = self.parent.rename_material(self, value)
        self.mark_modified()

    def setXluStr(self, str_value):
        val = validBool(str_value)
        if self.xlu != val:
            self.xlu = val
            self.setDrawXLU(val)
            self.mark_modified()

    # def setShader(self, shader):
    #     if shader.offset != self.shaderOffset + self.offset:
    #         self.shaderOffset = shader.offset - self.offset
    #         self.shaderStages = shader.countDirectStages()
    #         self.indirectStages = shader.countIndirectStages()
    #
    #     self.shader = shader
    #     return self.isModified

    def setShaderColorStr(self, str):
        i = str.find(':')
        if i < 0:
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        key = str[:i]
        value = str[i + 1:]
        isConstant = True if 'constant' in key else False
        if not key[-1].isdigit():
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        index = int(key[-1])
        if not 0 <= index <= 3 or (not isConstant) and index == 3:
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        intVals = parse_color(value)
        if not intVals:
            raise ValueError(self.SHADERCOLOR_ERROR.format(str))
        list = self.matGX.cctevRegs if isConstant else self.matGX.tevRegs
        list[index].setColor(intVals)
        self.mark_modified()

    def set_color(self, color, color_num=0):
        self.matGX.tevRegs[color_num].setColor(color)
        self.mark_modified()

    def setCullModeStr(self, cullstr):
        cullstr = cullstr.replace('cull', '')
        i = indexListItem(self.CULL_STRINGS, cullstr, self.cullmode)
        if i >= 0 and self.cullmode != i:
            self.cullmode = i
            self.mark_modified()

    def setLightChannelStr(self, lcStr):
        i = lcStr.find(':')
        if i < 0:
            raise ValueError(LightChannel.LC_ERROR)
        key = lcStr[:i]
        value = lcStr[i + 1:]
        self.lightChannels[0][key] = value
        self.mark_modified()

    def setLightsetStr(self, str):
        val = int(str)
        if val != -1:
            raise ValueError("Invalid lightset " + str + ", expected -1")
        if self.lightset != -1:
            self.lightset = -1
            self.mark_modified()

    def setFogsetStr(self, str):
        val = int(str)
        if val != 0:
            raise ValueError("Invalid fogset " + str + ", expected 0")
        if self.fogset != 0:
            self.fogset = 0
            self.mark_modified()

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
                self.mark_modified()
        elif val == -2:
            if not enabled:
                ca.setEnabled(True)
                self.mark_modified()
        else:
            if not enabled or ca.get() != val:
                ca.setEnabled(True)
                ca.set(val)
                self.mark_modified()

    def setMatrixModeStr(self, str):
        if "maya" in str:
            if self.textureMatrixMode != 0:
                self.textureMatrixMode = 0
        elif "xsi" in str:
            if self.textureMatrixMode != 1:
                self.textureMatrixMode = 1
        elif "3dsmax" in str:
            if self.textureMatrixMode != 2:
                self.textureMatrixMode = 2
        else:
            raise ValueError("Invalid Matrix Mode " + str + ", Expected Maya|XSI|3DSMax")
        self.mark_modified()

    def setRef0Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref0 must be 0-255")
        af = self.matGX.alphafunction
        if af.getRef0() != val:
            af.setRef0(val)
            self.mark_modified()

    def setRef1Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref1 must be 0-255")
        af = self.matGX.alphafunction
        if af.getRef1() != val:
            af.setRef1(val)
            self.mark_modified()

    def setComp0Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.alphafunction.getComp0())
        if i >= 0:
            self.matGX.alphafunction.setComp0(i)
            self.mark_modified()

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.alphafunction.getComp1())
        if i >= 0:
            self.matGX.alphafunction.setComp1(i)
            self.mark_modified()

    def setCompareBeforeTexStr(self, str):
        val = validBool(str)
        if val != self.compareBeforeTexture:
            self.compareBeforeTexture = val
            self.mark_modified()

    def setBlendStr(self, str):
        val = validBool(str)
        b = self.matGX.blendmode
        if val != b.isEnabled():
            b.setEnabled(val)
            self.mark_modified()

    def setBlendSrcStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLFACTOR_STRINGS, str, b.getSrcFactor())
        if i >= 0:
            b.setSrcFactor(i)
            self.mark_modified()

    def setBlendDestStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLFACTOR_STRINGS, str, b.getDstFactor())
        if i >= 0:
            b.setDstFactor(i)
            self.mark_modified()

    def setBlendLogicStr(self, str):
        b = self.matGX.blendmode
        i = indexListItem(self.BLLOGIC_STRINGS, str, b.getBlendLogic())
        if i >= 0:
            b.setBlendLogic(i)
            self.mark_modified()

    def setEnableDepthTestStr(self, str):
        val = validBool(str)
        d = self.matGX.zmode
        if val != d.getDepthTest():
            d.setDepthTest(val)
            self.mark_modified()

    def setEnableDepthUpdateStr(self, str):
        val = validBool(str)
        d = self.matGX.zmode
        if val != d.getDepthUpdate():
            d.setDepthUpdate(val)
            self.mark_modified()

    def setDepthFunctionStr(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.matGX.zmode.getDepthFunction())
        d = self.matGX.zmode
        if i >= 0:
            d.setDepthFunction(i)
            self.mark_modified()

    def setDrawPriorityStr(self, str):
        i = validInt(str, 0, 255)
        for x in self.polygons:
            x.set_draw_priority(i)

    def setDrawXLU(self, enabled):
        if enabled != self.xlu:
            self.xlu = enabled
            self.mark_modified()

    MATRIX_ERR = 'Error parsing "{}", Usage: IndirectMatrix:[<i>:]<scale>,<r1c1>,<r1c2>,<r1c3>,<r2c1>,<r2c2>,<r2c3>'

    def setIndirectMatrix(self, str_value):
        matrix_index = 0
        colon_index = str_value.find(':')
        if colon_index > -1:
            matrix_index = validInt(str_value[0], 0, 3)
            str_value = str_value[colon_index + 1:]
        if ',' not in str_value:
            try:
                enable = validBool(str_value)
                self.matGX.setIndMatrixEnable(matrix_index, enable)
                return
            except ValueError as e:
                raise ValueError(self.MATRIX_ERR.format(str_value))
        str_values = str_value.replace('scale', '').split(',')
        if len(str_values) != 7:
            raise ValueError(self.MATRIX_ERR.format(str_value))
        scale = validInt(str_values.pop(0).strip(':'), -17, 47)
        matrix = [validFloat(x.strip('()'), -1, 1) for x in str_values]
        self.matGX.setIndMatrix(matrix_index, scale, matrix)
        self.mark_modified()

    def setLayerCountStr(self, str_value):
        self.setLayerCount(validInt(str_value, 0, 8))

    def setLayerCount(self, val):
        current_len = len(self.layers)
        if val > current_len:
            while val > current_len:
                current_len = self.addEmptyLayer()
            self.mark_modified()
        elif val < current_len:
            while val < current_len:
                current_len = self.removeLayerI()
            self.mark_modified()

    # Set functions
    SET_SETTING = (setXluStr, setRef0Str, setRef1Str,
                   setComp0Str, setComp1Str, setCompareBeforeTexStr, setBlendStr, setBlendSrcStr,
                   setBlendLogicStr, setBlendDestStr, setConstantAlphaStr, setCullModeStr,
                   setShaderColorStr, setLightChannelStr, setLightsetStr,
                   setFogsetStr, setMatrixModeStr, setEnableDepthTestStr,
                   setEnableDepthUpdateStr, setDepthFunctionStr, setDrawPriorityStr,
                   setIndirectMatrix, rename, setLayerCountStr)

    # --------------------- threshold transparency -------------------------------
    def get_transparency_threshold(self):
        return self.matGX.alphafunction.get_alpha_value()

    def set_transparency_threshold(self, value):
        if self.matGX.alphafunction.get_alpha_value() != value:
            self.matGX.alphafunction.set_alpha_value(value)
            self.compareBeforeTexture = (value <= 0)
            self.mark_modified()

    # ----------------------- color ------------------------------------------------
    def get_colors_used(self):
        """Check shader and finds colors used (vertex colors, light colors, shader colors)"""
        raise NotImplementedError()

    def get_tex0s(self):
        tex0s = []
        if len(self.layers) <= 0:
            return tex0s
        tex_map = self.get_texture_map()
        for x in self.layers:
            map = tex_map.get(x.name)
            if map is not None:
                tex0s.append(map)
        return tex0s

    def get_uv_channels(self):
        channels = {x.get_uv_channel() for x in self.layers}
        if None in channels:
            channels.remove(None)
        return channels


    # ------------------------- SRT0 --------------------------------------------------
    def add_srt0(self):
        """Adds a new srt0 with one layer reference"""
        if self.srt0:
            return self.srt0
        anim = self.parent.add_srt0(self)
        self.set_srt0(anim)
        anim.addLayer()
        self.mark_modified()
        return anim

    def remove_srt0(self):
        if self.srt0:
            self.parent.remove_srt0(self.srt0)
            self.mark_modified()
            self.srt0 = None

    def set_srt0(self, anim):
        """This is called by model to set up the srt0 reference"""
        if self.srt0:
            AutoFix.get().error('Multiple Srt0 for {}'.format(self.name), 1)
            return False
        self.srt0 = anim
        anim.setMaterial(self)
        return True

    def get_srt0(self):
        """Gets the srt0, if force_add is set, automatically generates one"""
        # if not self.srt0 and force_add:
        #     self.srt0 = self.parent.add_srt0(self)
        return self.srt0

    def has_srt0(self):
        return self.srt0 is not None

    # ----------------------------PAT0 ------------------------------------------
    def has_pat0(self):
        return self.pat0 is not None

    def add_pat0(self):
        """Adds a new pat0"""
        if self.pat0:
            return self.pat0
        anim = self.parent.add_pat0(self)
        self.set_pat0(anim)
        self.mark_modified()
        return anim

    def remove_pat0(self):
        if self.pat0:
            self.parent.remove_pat0(self.pat0)
            self.pat0 = None
            self.mark_modified()

    def set_pat0(self, anim):
        if self.pat0:
            AutoFix.get().error('Multiple Pat0 for {}!'.format(self.name), 1)
            return False
        self.pat0 = anim
        return True

    def get_pat0(self):
        return self.pat0

    def disable_blend(self):
        if self.is_blend_enabled():
            self.matGX.blendmode.setEnabled(False)
            self.setXluStr('false')
            self.matGX.zmode.setDepthUpdate(True)
            self.setDrawPriorityStr('0')
            self.mark_modified()

    def enable_blend(self, enabled=True):
        if enabled:
            if not self.is_blend_enabled():
                self.compareBeforeTexture = True
                self.matGX.blendmode.setEnabled(True)
                self.setXluStr('true')
                self.matGX.alphafunction.enable(False)
                self.matGX.zmode.setDepthUpdate(False)
                self.setDrawPriorityStr('1')
                self.mark_modified()
        else:
            self.disable_blend()

    def is_blend_enabled(self):
        return self.matGX.blendmode.isEnabled()

    # ----------------------------INFO ------------------------------------------
    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + self.name if indentation_level else '>' + self.parent.name + "->" + self.name
        if key in self.SETTINGS:
            val = self.getKey(key)
            if val is not None:
                print("{}\t{}:{}".format(trace, key, val))
            return
        elif not key:
            print("{}\txlu:{} cull:{}".format(trace, self.xlu, self.CULL_STRINGS[self.cullmode]))
        indentation_level += 1
        for x in self.layers:
            x.info(key, indentation_level)

    # ------------------------------------- Check ----------------------------------------
    def check(self, texture_map=None):
        if texture_map is None:
            texture_map = self.get_texture_map()
        for layer in self.layers:
            layer.check(texture_map)
        self.shader.check()
        if self.pat0:
            self.pat0.check()
        if self.srt0:
            self.srt0.check()

    def check_shader(self, direct_count, ind_count, matrices_used):
        # checks with shader
        for i in range(2):
            matrix = self.matGX.getIndMatrix(i)
            if matrix.enabled:
                if not matrices_used[i]:
                    AutoFix.get().warn('{} indirect matrix {} enabled but unused in shader'.format(self.name, i), 3)
            elif not matrix.enabled and matrices_used[i]:
                AutoFix.get().warn('{} indirect matrix {} disabled but used in shader'.format(self.name, i), 3)
        if direct_count != self.shaderStages:
            self.shaderStages = direct_count
            self.mark_modified()
        if ind_count != self.indirectStages:
            self.indirectStages = ind_count
            self.mark_modified()

    # -------------------------------- Layer removing/adding --------------------------
    def removeLayerI(self, index=-1):
        """Removes layer at index"""
        layer = self.layers[index]
        self.parent.remove_texture_link(layer.name)
        self.layers.pop(index)
        if self.srt0:
            self.srt0.removeLayerI(index)
        self.mark_modified()
        return len(self.layers)

    def removeLayer(self, name):
        """ Removes layer from material by name """
        for i, x in enumerate(self.layers):
            if x.name == name:
                self.removeLayerI(i)
                self.mark_modified()
                return
        raise ValueError('Material "{}" has no layer "{}" to remove'.format(self.name, name))

    def addEmptyLayer(self):
        """Adds 1 layer"""
        self.addLayer('Null')
        return len(self.layers)

    def addLayer(self, name):
        """ Creates and returns new layer """
        i = len(self.layers)
        l = Layer(i, name, self)
        self.layers.append(l)
        if self.srt0:
            self.srt0.updateLayerNameI(i, name)
        self.mark_modified()
        return l

    def mark_unmodified(self):
        self.is_modified = False
        self._mark_unmodified_group(self.layers)
        self.shader.mark_unmodified()
        if self.pat0:
            self.pat0.mark_unmodified()
        if self.srt0:
            self.srt0.mark_unmodified()

    def renameLayer(self, layer, name):
        if self.srt0:
            self.srt0.updateLayerNameI(layer.layer_index, name)
        return self.parent.rename_texture_link(layer, name)

    def get_first_layer_name(self):
        if self.layers:
            return self.layers[0].name

    def is_vertex_color_enabled(self):
        return self.lightChannels[0].is_vertex_color_enabled()

    def enable_vertex_color(self, enable=True):
        if self.lightChannels[0].enable_vertex_color(enable):
            self.mark_modified()

    # ---------------------------------PASTE------------------------------------------
    def paste(self, item):
        self.paste_layers(item)
        self.shader.paste(item.shader)
        # animations
        if item.srt0:
            self.add_srt0()
            self.srt0.paste(item.srt0)
        else:
            self.remove_srt0()
        if item.pat0:
            self.add_pat0()
            self.pat0.paste(item.pat0)
        else:
            self.remove_pat0()
        self.paste_data(item)
        self.mark_modified()

    def paste_data(self, item):
        self.xlu = item.xlu
        self.setDrawXLU(self.xlu)
        self.shaderStages = item.shaderStages
        self.indirectStages = item.indirectStages
        self.cullmode = item.cullmode
        self.compareBeforeTexture = item.compareBeforeTexture
        self.lightset = item.lightset
        self.fogset = item.fogset
        self.matGX = deepcopy(item.matGX)
        self.lightChannels = deepcopy(item.lightChannels)

    def paste_layers(self, item):
        my_layers = self.layers
        item_layers = item.layers
        num_layers = len(item_layers)
        self.setLayerCount(num_layers)
        for i in range(num_layers):
            my_layers[i].paste(item_layers[i])
            my_layers[i].setName(item_layers[i].name)

    # -----------------------------------------------------------------------------
    # PACKING
    # -----------------------------------------------------------------------------
    def pack(self, binfile, texture_link_map=None):
        """ Packs the material """
        self.offset = binfile.start()
        binfile.markLen()
        binfile.write("i", binfile.getOuterOffset())
        binfile.storeNameRef(self.name)
        binfile.write("2I4BI3b", self.index, self.xlu << 31, len(self.layers), len(self.lightChannels),
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
        channels = self.lightChannels
        for i in range(2):
            if i < len(channels):
                channels[i].pack(binfile)
            else:
                LightChannel.pack_default(binfile)
        binfile.createRef(1)
        for l in layers:
            # Write Texture linker offsets
            start_offset = texture_link_map[l.name]
            tex_link_offsets = binfile.references[start_offset]
            binfile.writeOffset('i', tex_link_offsets.pop(0), self.offset - start_offset)  # material offset
            binfile.writeOffset('i', tex_link_offsets.pop(0), binfile.offset - start_offset)  # layer offset
            l.pack(binfile)

        binfile.alignToParent()
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
            layer = Layer(len(self.layers), binfile.unpack_name(), self)
            self.layers.append(layer)
            layer.unpack(binfile, scale_offset)
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
        [self.textureMatrixMode] = binfile.read('I', 4)
        # Texture matrix
        binfile.advance(160)
        for layer in self.layers:
            layer.unpack_textureMatrix(binfile)
        return offset

    def unpackLightChannels(self, binfile, nlights):
        """ Unpacks the light channels """
        for i in range(nlights):
            self.lightChannels.append(LightChannel(binfile))

    def unpack(self, binfile):
        """ Unpacks material """
        offset = binfile.start()
        # print('Material {} offset {}'.format(self.name, offset))
        binfile.readLen()
        binfile.advance(8)
        self.index, xluFlags, ntexgens, nlights, \
        self.shaderStages, self.indirectStages, \
        self.cullmode, self.compareBeforeTexture, \
        self.lightset, self.fogset, pad = binfile.read("2I2B2BI4b", 20)
        self.xlu = xluFlags >> 31 & 1
        assert (xluFlags & 0x7fffffff) == 0
        assert nlights <= 2
        binfile.advance(8)
        self.shaderOffset, nlayers = binfile.read("2i", 8)
        if nlayers != ntexgens:
            raise Exception('Number of layers {} is different than number texgens {}'.format(nlayers, ntexgens))
        self.shaderOffset += binfile.beginOffset
        binfile.store()  # layer offset
        if self.parent.version >= 10:
            binfile.advance(8)
            # bo = binfile.offset
            # [dpo] = binfile.readOffset("I", binfile.offset)
            binfile.store()  # store matgx offset
        else:
            binfile.advance(4)
            binfile.store()  # store matgx offset
            # binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        startlayerInfo = binfile.offset
        # [self.textureMatrixMode] = binfile.readOffset('I', binfile.offset + 4)
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
    LC_ERROR = 'Invalid Light "{}", Expected ((color|alpha)control:key:value|[material|ambient|raster]\
(color|alpha)(enable|rgba))'

    def __init__(self, binfile=None):
        if binfile:
            self.unpack(binfile)
        else:
            self.begin()

    def begin(self):
        self.materialColorEnabled = self.materialAlphaEnabled = True
        self.ambientAlphaEnabled = self.ambientColorEnabled = True
        self.rasterAlphaEnabled = self.rasterColorEnabled = True
        self.materialColor = [128, 128, 128, 255]
        self.ambientColor = [0, 0, 0, 255]
        self.colorLightControl = self.LightChannelControl(0x700)
        self.alphaLightControl = self.LightChannelControl(0x700)

    def __str__(self):
        return 'Flags:{:02X} Mat:{} Amb:{}\n\tColorControl: {}\n\tAlphaControl: {}'.format(self.flagsToInt(),
                                                                                           self.materialColor,
                                                                                           self.ambientColor,
                                                                                           self.colorLightControl,
                                                                                           self.alphaLightControl)

    def enable_vertex_color(self, enabled=True):
        return self.colorLightControl.enable_vertex_color(enabled) or \
            self.alphaLightControl.enable_vertex_color(enabled)

    def is_vertex_color_enabled(self):
        return self.colorLightControl.is_vertex_color_enabled() and \
            self.alphaLightControl.is_vertex_color_enabled()

    def __getitem__(self, item):
        is_color = True if "color" in item else False
        if "control" in item:
            return self.colorLightControl[item] if is_color else self.alphaLightControl[item]
        elif 'enable' in item:
            if "material" in item:
                return self.materialColorEnabled if is_color else self.materialAlphaEnabled
            elif "ambient" in item:
                return self.ambientColorEnabled if is_color else self.ambientAlphaEnabled
            elif "raster" in item:
                return self.rasterColorEnabled if is_color else self.rasterAlphaEnabled
        else:
            if 'material' in item:
                return self.materialColor
            elif 'ambient' in item:
                return self.ambientColor
        raise ValueError(self.LC_ERROR.format(item))

    def __setitem__(self, key, value):
        is_color = True if "color" in key else False
        if "control" in key:
            key2, value = splitKeyVal(value)
            if not key2:
                raise ValueError(self.LC_ERROR.format(key))
            if is_color:
                self.colorLightControl[key2] = value
            else:
                self.alphaLightControl[key2] = value
        elif 'enable' in key:
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
        else:
            int_vals = parse_color(value)
            if not int_vals:
                raise ValueError(self.LC_ERROR.format(key))
            if "material" in key:
                self.materialColor = int_vals
            elif "ambient" in key:
                self.ambientColor = int_vals
            else:
                raise ValueError(self.LC_ERROR.format(key))

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

        def is_vertex_color_enabled(self):
            return self.materialSourceVertex

        def enable_vertex_color(self, enable):
            if self.materialSourceVertex != enable:
                self.materialSourceVertex = enable
                return True
            return False

        def __str__(self):
            return 'enabled:{} material:{} ambient:{} diffuse:{} attenuation:{}'.format(self['enable'],
                                                                                        self['material'],
                                                                                        self['ambient'],
                                                                                        self['diffuse'],
                                                                                        self['attenuation'])

        def __getitem__(self, item):
            if 'material' in item:
                return self.LIGHT_SOURCE[self.materialSourceVertex]
            elif 'enable' in item:
                return self.enabled
            elif 'ambient' in item:
                return self.LIGHT_SOURCE[self.ambientSourceVertex]
            elif 'diffuse' in item:
                return self.DIFFUSE_FUNCTION[self.diffuseFunction]
            elif 'attenuation' in item:
                return 'None' if not self.attenuationEnabled else self.ATTENUATION[self.attenuationFunction]
            else:
                raise ValueError(LightChannel.LC_ERROR.format(item))

        def __setitem__(self, key, value):
            if 'material' in key:
                i = indexListItem(self.LIGHT_SOURCE, value, self.materialSourceVertex)
                if i >= 0:
                    self.materialSourceVertex = i
            elif 'enable' in key:
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
                raise ValueError(LightChannel.LC_ERROR.format(key))

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

    def flagsToInt(self):
        return self.materialColorEnabled | self.materialAlphaEnabled << 1 | self.ambientColorEnabled << 2 \
               | self.ambientAlphaEnabled << 3 | self.rasterColorEnabled << 4 | self.rasterAlphaEnabled << 5

    def pack(self, binfile):
        flags = self.flagsToInt()
        mc = self.materialColor
        binfile.write('I4B', flags, mc[0], mc[1], mc[2], mc[3])
        ac = self.ambientColor
        binfile.write('4B2I', ac[0], ac[1], ac[2], ac[3],
                      self.colorLightControl.getFlagsAsInt(), self.alphaLightControl.getFlagsAsInt())

    @staticmethod
    def pack_default(binfile):
        binfile.write('5I', 0xf, 0xff, 0, 0, 0)
