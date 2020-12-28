#!/usr/bin/Python
# ---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
# ---------------------------------------------------------------------
import re
from copy import deepcopy

from abmatt.brres.lib.matching import validBool, indexListItem, validInt, validFloat, MATCHING, parse_color
from abmatt.brres.lib.node import Clipable
from abmatt.brres.mdl0.material.layer import Layer
from abmatt.brres.mdl0.shader import Shader
from abmatt.autofix import AutoFix
from abmatt.brres.mdl0.material.light import LightChannel

# Constants
from abmatt.brres.mdl0.wiigraphics.bp import IndMatrix

ALPHA_LOGIC_AND = 0
ALPHA_LOGIC_OR = 1
ALPHA_LOGIC_XOR = 2
ALPHA_LOGIC_IXOR = 3

COMP_NEVER = 0
COMP_LESS_THAN = 1
COMP_EQUAL = 2
COMP_LESS_THAN_OR_EQUAL = 3
COMP_GREATER_THAN = 4
COMP_NOT_EQUAL = 5
COMP_GREATER_OR_EQUAL = 6
COMP_ALWAYS = 7

BLEND_MODE_NONE = 0
BLEND_MODE_BLEND = 1
BLEND_MODE_LOGIC = 2
BLEND_MODE_SUBTRACT = 3

BLEND_LOGIC_CLEAR = 0
BLEND_LOGIC_AND = 1
BLEND_LOGIC_REVERSE_AND = 2
BLEND_LOGIC_COPY = 3
BLEND_LOGIC_INVERSE_AND = 4
BLEND_LOGIC_NO_OP = 5
BLEND_LOGIX_XOR = 6
BLEND_LOGIC_OR = 7
BLEND_LOGIC_NOR = 8
BLEND_LOGIC_EQUIVALENT = 9
BLEND_LOGIC_INVERSE = 10
BLEND_LOGIC_REVERSE_OR = 11
BLEND_LOGIC_INVERSE_COPY = 12
BLEND_LOGIC_INVERSE_OR = 13
BLEND_LOGIC_NAND = 14
BLEND_LOGIC_SET = 15

BLEND_FACTOR_ZERO = 0
BLEND_FACTOR_ONE = 1
BLEND_FACTOR_SOURCE_COLOR = 2
BLEND_FACTOR_INVERSE_SOURCE_COLOR = 3
BLEND_FACTOR_SOURCE_ALPHA = 4
BLEND_FACTOR_INVERSE_SOURCE_ALPHA = 5
BLEND_FACTOR_DEST_ALPHA = 6
BLEND_FACTOR_INVERSE_DEST_ALPHA = 7

CULL_NONE = 0
CULL_OUTSIDE = 1
CULL_INSIDE = 2
CULL_ALL = 3


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
    LOGIC_STRINGS = ('and', 'or', 'exclusiveor', 'invexclusiveor')
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
        super(Material, self).__init__(name, parent, binfile)

    def __deepcopy__(self, memodict={}):
        raise NotImplementedError()  # too many issues with tightly linked parent
        # don't copy references copied elsewhere
        # srt0 = self.srt0
        # self.srt0 = None
        # pat0 = self.pat0
        # self.pat0 = None
        # shader = self.shader
        # self.shader = None
        # polygons = self.polygons
        # self.polygons = None
        # copy = super().__deepcopy__(memodict)
        # self.srt0 = srt0
        # self.pat0 = pat0
        # self.shader = shader
        # self.polygons = polygons
        copy = Material(self.name)
        copy.paste(self)
        return copy

    def set_default_color(self):
        self.set_color(self.DEFAULT_COLOR)

    @staticmethod
    def get_unique_material(name, mdl):
        is_digit = False
        while True:
            mat = mdl.get_material_by_name(name)
            if not mat:
                return Material(name, mdl)
            if not is_digit and not name[-1].isdigit():
                name = name + '1'
                is_digit = True
            else:
                name = re.sub('\d+$', lambda x: str(int(x.group(0)) + 1), name)

    def begin(self):
        self.shaderStages = 0
        self.indirectStages = 0
        self.cullmode = CULL_INSIDE
        self.compareBeforeTexture = True
        self.lightset = -1
        self.fogset = 0
        self.xlu = False
        self.textureMatrixMode = 0
        self.indirect_matrices = [IndMatrix() for i in range(3)]
        self.lightChannels.append(LightChannel())
        self.shader = Shader(self.name, self)
        self.ref0 = 0
        self.ref1 = 0
        self.comp0 = COMP_ALWAYS
        self.comp1 = COMP_ALWAYS
        self.logic = ALPHA_LOGIC_AND
        self.depth_test = True
        self.depth_update = True
        self.depth_function = COMP_LESS_THAN_OR_EQUAL
        self.blend_enabled = False
        self.blend_logic_enabled = False
        self.blend_dither = False
        self.blend_update_color = False
        self.blend_update_alpha = False
        self.blend_subtract = False
        self.blend_logic = BLEND_LOGIC_COPY
        self.blend_source = BLEND_FACTOR_SOURCE_ALPHA
        self.blend_dest = BLEND_FACTOR_INVERSE_SOURCE_ALPHA
        self.constant_alpha = 0
        self.constant_alpha_enabled = False
        self.colors = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        self.constant_colors = [(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)]
        self.ras1_ss = [0] * 2

    def auto_detect_layer(self):
        if not self.layers:
            if self.name in self.get_texture_map():
                self.addLayer(self.name)

    def __str__(self):
        return "{}: xlu {} layers {} culling {} blend {}".format(self.name,
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
        return self.ref0

    def getRef1(self):
        return self.ref1

    def getComp0(self):
        return self.COMP_STRINGS[self.comp0]

    def getComp1(self):
        return self.COMP_STRINGS[self.comp1]

    def getLogic(self):
        return self.LOGIC_STRINGS[self.logic]

    def getCompareBeforeTexture(self):
        return self.compareBeforeTexture

    def getBlend(self):
        return self.blend_enabled

    def getBlendSrc(self):
        return self.BLFACTOR_STRINGS[self.blend_source]

    def getBlendLogic(self):
        return self.BLLOGIC_STRINGS[self.blend_logic]

    def getBlendDest(self):
        return self.BLFACTOR_STRINGS[self.blend_dest]

    def getConstantAlpha(self):
        if not self.constant_alpha_enabled:
            return -1
        return self.constant_alpha

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
        return self.colors[i]

    def getConstantColor(self, i):
        return self.constant_colors[i]

    def getBrres(self):
        parent = self.parent
        if parent:
            return parent.parent

    def getShaderColor(self):
        ret = ""
        for i in range(3):
            ret += "Color{}: {}\t".format(i, self.getColor(i))
        ret += "\n\t"
        for i in range(4):
            ret += "Const{}: {}\t".format(i, self.getConstantColor(i))
        return ret

    def getMatrixMode(self):
        return self.MATRIXMODE[self.textureMatrixMode]

    def getEnableDepthTest(self):
        return self.depth_test

    def getEnableDepthUpdate(self):
        return self.depth_update

    def getDepthFunction(self):
        return self.COMP_STRINGS[self.depth_function]

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

    def isIndMatrixEnabled(self, id=0):
        return self.indirect_matrices[id].enabled

    def getIndMatrixScale(self, id=0):
        return self.indirect_matrices[id].scale

    def getIndMatrix(self, id=0):
        return self.indirect_matrices[id].matrix

    def getIndMatrixStr(self, id=0):
        matrix = self.indirect_matrices[id]
        enabled = 'enabled' if matrix.enabled else 'disabled'
        ret = '{}: {} Scale {}, {}'.format(id, enabled, matrix.scale, matrix.matrix)
        return ret

    def getLayerCount(self):
        return len(self.layers)

    # Get Functions
    GET_SETTING = (getXlu, getRef0, getRef1, getComp0, getComp1, getCompareBeforeTexture,
                   getBlend, getBlendSrc, getBlendLogic, getBlendDest, getConstantAlpha, getCullMode,
                   getShaderColor, getLightChannel, getLightset, getFogset, getMatrixMode, getEnableDepthTest,
                   getEnableDepthUpdate, getDepthFunction, getDrawPriority, getIndMatrixStr, getName, getLayerCount)

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
        list = self.constant_colors if isConstant else self.colors
        list[index] = intVals
        self.mark_modified()

    def set_color(self, color, color_num=0):
        if self.colors[color_num] != color:
            self.colors[color_num] = color
            self.mark_modified()

    def set_constant_color(self, color, color_num=0):
        if self.constant_colors[color_num] != color:
            self.constant_colors[color_num] = color
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

    def enable_constant_alpha(self, enable=True):
        if enable != self.constant_alpha_enabled:
            self.constant_alpha_enabled = enable
            self.mark_modified()

    def set_constant_alpha(self, val):
        if val != self.constant_alpha:
            self.constant_alpha = val
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
        enabled = self.constant_alpha_enabled
        if val == -1:
            if enabled:
                self.constant_alpha_enabled = False
                self.mark_modified()
        elif val == -2:
            if not enabled:
                self.constant_alpha_enabled = True
                self.mark_modified()
        else:
            if not enabled or self.constant_alpha != val:
                self.constant_alpha_enabled = True
                self.constant_alpha = val
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
        if self.ref0 != val:
            self.ref0 = val
            self.mark_modified()

    def setRef1Str(self, str):
        val = int(str)
        if not 0 <= val < 256:
            raise ValueError("Ref1 must be 0-255")
        if self.ref1 != val:
            self.ref1 = val
            self.mark_modified()

    def setComp0Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp0)
        if i >= 0:
            self.comp0 = i
            self.mark_modified()

    def setComp1Str(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.comp1)
        if i >= 0:
            self.comp1 = i
            self.mark_modified()

    def setLogic(self, str):
        i = indexListItem(self.LOGIC_STRINGS, str, self.logic)
        if i >= 0:
            self.logic = i
            self.mark_modified()

    def setCompareBeforeTex(self, val):
        if val != self.compareBeforeTexture:
            self.compareBeforeTexture = val
            self.mark_modified()

    def setCompareBeforeTexStr(self, str):
        self.setCompareBeforeTex(validBool(str))

    def enable_xlu(self, enable):
        if self.xlu != enable:
            self.xlu = enable
            self.mark_modified()

    def setBlendStr(self, str):
        val = validBool(str)
        if val != self.blend_enabled:
            self.blend_enabled = val
            self.mark_modified()

    def enableBlendFlag(self, enable):
        if self.blend_enabled != enable:
            self.blend_enabled = enable
            self.mark_modified()

    def setBlendSrcStr(self, str):
        i = indexListItem(self.BLFACTOR_STRINGS, str, self.blend_source)
        if i >= 0:
            self.blend_source = i
            self.mark_modified()

    def setBlendDestStr(self, str):
        i = indexListItem(self.BLFACTOR_STRINGS, str, self.blend_dest)
        if i >= 0:
            self.blend_dest = i
            self.mark_modified()

    def setBlendLogicStr(self, str):
        i = indexListItem(self.BLLOGIC_STRINGS, str, self.blend_logic)
        if i >= 0:
            self.blend_logic = i
            self.mark_modified()

    def enableBlendLogic(self, enabled):
        if self.blend_logic_enabled != enabled:
            self.blend_logic_enabled = enabled
            self.mark_modified()

    def setEnableDepthTest(self, val):
        if val != self.depth_test:
            self.depth_test = val
            self.mark_modified()

    def setEnableDepthTestStr(self, str):
        self.setEnableDepthTest(validBool(str))

    def setEnableDepthUpdate(self, val):
        if val != self.depth_update:
            self.depth_update = val
            self.mark_modified()

    def setEnableDepthUpdateStr(self, str):
        self.setEnableDepthUpdate(validBool(str))

    def setDepthFunctionStr(self, str):
        i = indexListItem(self.COMP_STRINGS, str, self.depth_function)
        if i >= 0:
            self.depth_function = i
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

    def setIndMatrixEnable(self, id=0, enable=True):
        x = self.indirect_matrices[id]
        x.enabled = enable
        if enable and not x.scale:
            # set up a default
            x.scale = 14
            x.matrix = [[0.6396484375, 0, 0], [0, 0.639648375, 0]]

    def setIndMatrixScale(self, scale, id=0):
        matrix = self.indirect_matrices[id]
        if not -17 <= scale < 47:
            raise ValueError('Indirect scale {} out of range!'.format(scale))
        if matrix.scale != scale:
            matrix.scale = scale
            self.mark_modified()

    def setIndMatrix(self, matrix, id=0):
        my_matrix = self.indirect_matrices[id].matrix
        modify_flag = False
        if len(matrix) != 2 or len(matrix[0]) != 3:
            raise ValueError('Ind Matrix has incorrect shape! ' + str(matrix))
        for i in range(2):
            for j in range(3):
                if my_matrix[i][j] != matrix[i][j]:
                    my_matrix[i][j] = matrix[i][j]
                    modify_flag = True
        if modify_flag:
            self.mark_modified()

    def setIndirectMatrixStr(self, str_value):
        matrix_index = 0
        colon_index = str_value.find(':')
        if colon_index > -1:
            matrix_index = validInt(str_value[0], 0, 3)
            str_value = str_value[colon_index + 1:]
        if ',' not in str_value:
            try:
                enable = validBool(str_value)
                self.setIndMatrixEnable(matrix_index, enable)
                return
            except ValueError as e:
                raise ValueError(self.MATRIX_ERR.format(str_value))
        str_values = str_value.replace('scale', '').split(',')
        if len(str_values) != 7:
            raise ValueError(self.MATRIX_ERR.format(str_value))
        scale = validInt(str_values.pop(0).strip(':'), -17, 47)
        matrix = [validFloat(x.strip('()'), -1, 1) for x in str_values]
        ind_matrix = self.indirect_matrices[matrix_index]
        ind_matrix.matrix = matrix
        ind_matrix.scale = scale
        ind_matrix.enabled = True
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
                   setIndirectMatrixStr, rename, setLayerCountStr)

    # --------------------- threshold transparency -------------------------------
    def get_transparency_threshold(self):
        if self.comp0 == COMP_GREATER_OR_EQUAL and self.comp1 == COMP_LESS_THAN_OR_EQUAL:
            return self.ref0
        return 0

    def set_transparency_threshold(self, value):
        if self.get_transparency_threshold() != value:
            if value:
                self.ref0 = value
                self.comp0 = COMP_GREATER_OR_EQUAL
                self.ref1 = 255
                self.comp1 = COMP_LESS_THAN_OR_EQUAL
                self.compareBeforeTexture = False
            else:
                self.ref0 = 0
                self.comp0 = COMP_ALWAYS
                self.ref1 = 0
                self.comp1 = COMP_ALWAYS
                self.compareBeforeTexture = True
            self.mark_modified()

    def get_tex0s(self):
        tex0s = []
        if len(self.layers) <= 0:
            return tex0s
        tex_map = self.get_texture_map()
        for x in self.layers:
            tex = tex_map.get(x.name)
            if tex is not None:
                tex0s.append(tex)
        return tex0s

    def get_uv_channels(self):
        channels = {x.get_uv_channel() for x in self.layers}
        if None in channels:
            channels.remove(None)
        return channels

    def get_animation(self):
        if self.srt0 is not None:
            return self.srt0
        elif self.pat0 is not None:
            return self.pat0

    def remove_animation(self):
        if self.srt0 is not None:
            self.remove_srt0()
        elif self.pat0 is not None:
            self.remove_pat0()

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
            self.srt0 = None
            self.mark_modified()

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
            AutoFix.get().error('Multiple Pat0 for {} in {}!'.format(self.name, self.getBrres().name), 1)
            return False
        self.pat0 = anim
        return True

    def get_pat0(self):
        return self.pat0

    def disable_blend(self):
        if self.is_blend_enabled():
            self.blend_enabled = False
            self.xlu = False
            self.depth_update = True
            self.setDrawPriorityStr('0')
            self.mark_modified()

    def enable_blend(self, enabled=True):
        if enabled:
            if not self.is_blend_enabled():
                self.compareBeforeTexture = True
                self.blend_enabled = True
                self.xlu = True
                self.set_transparency_threshold(0)
                self.depth_update = False
                self.setDrawPriorityStr('1')
                self.mark_modified()
        else:
            self.disable_blend()

    def is_blend_enabled(self):
        return self.blend_enabled

    # ----------------------------INFO ------------------------------------------
    def info(self, key=None, indentation_level=0):
        trace = '>' + '  ' * indentation_level + self.name if indentation_level else '>' \
                                                                                     + self.parent.name + "->" + self.name
        if key in self.SETTINGS:
            val = self.getKey(key)
            if val is not None:
                AutoFix.get().info("{}\t{}:{}".format(trace, key, val), 1)
            return
        elif not key:
            AutoFix.get().info("{}\txlu:{} cull:{}".format(trace, self.xlu, self.CULL_STRINGS[self.cullmode]), 1)
        indentation_level += 1
        for x in self.layers:
            x.info(key, indentation_level)
        if self.srt0:
            self.srt0.info(key, indentation_level)
        elif self.pat0:
            self.pat0.info(key, indentation_level)

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
            matrix = self.indirect_matrices[i]
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
        l = Layer(name, self)
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
        if self.parent:
            self.parent.rename_texture_link(layer, name)
        layer.rename(name)
        return name

    def get_first_layer_name(self):
        if self.layers:
            return self.layers[0].name

    def is_vertex_color_enabled(self):
        return self.lightChannels[0].is_vertex_color_enabled()

    def enable_vertex_color(self, enable=True):
        if self.lightChannels[0].enable_vertex_color(enable):
            self.mark_modified()

    def get_material_color(self):
        return self.lightChannels[0].materialColor

    def set_material_color(self, color):
        assert len(color) == 4
        light = self.lightChannels[0]
        if light.materialColor != color:
            light.materialColor = color
            self.mark_modified()

    def get_ambient_color(self):
        return self.lightChannels[0].ambientColor

    def set_ambient_color(self, color):
        assert len(color) == 4
        light = self.lightChannels[0]
        if light.ambientColor != color:
            light.ambientColor = color
            self.mark_modified()

    def get_colors_used(self):
        """Returns the colors used, which is a list of
            a. tuples or
            b. string 'vertex' for vertex colors
        """
        ret = set()
        colors_used = self.shader.get_colors_used()
        for x in colors_used:
            if x.startswith('color'):
                is_constant = len(x) > 6
                index = int(x[5])
                colors = self.colors if not is_constant else self.constant_colors
                ret.add((x, colors[index]))
            elif x == 'lightchannel0':
                if self.is_vertex_color_enabled():
                    ret.add('vertex')
        return ret

    def __eq__(self, item):
        return self is item or (item is not None and type(self) == type(item) and \
                                self.name == item.name and item is not None and self.xlu == item.xlu and \
                                self.shaderStages == item.shaderStages and \
                                self.indirectStages == item.indirectStages and \
                                self.cullmode == item.cullmode and \
                                self.compareBeforeTexture == item.compareBeforeTexture and \
                                self.lightset == item.lightset and \
                                self.fogset == item.fogset and \
                                self.ref0 == item.ref0 and \
                                self.ref1 == item.ref1 and \
                                self.comp0 == item.comp0 and \
                                self.comp1 == item.comp1 and \
                                self.logic == item.logic and \
                                self.depth_test == item.depth_test and \
                                self.depth_update == item.depth_update and \
                                self.depth_function == item.depth_function and \
                                self.blend_enabled == item.blend_enabled and \
                                self.blend_logic_enabled == item.blend_logic_enabled and \
                                self.blend_dither == item.blend_dither and \
                                self.blend_update_color == item.blend_update_color and \
                                self.blend_update_alpha == item.blend_update_alpha and \
                                self.blend_subtract == item.blend_subtract and \
                                self.blend_logic == item.blend_logic and \
                                self.blend_source == item.blend_source and \
                                self.blend_dest == item.blend_dest and \
                                self.constant_alpha_enabled == item.constant_alpha_enabled and \
                                self.constant_alpha == item.constant_alpha and \
                                self.colors == item.colors and \
                                self.constant_colors == item.constant_colors and \
                                self.ras1_ss == item.ras1_ss and \
                                self.indirect_matrices == item.indirect_matrices and \
                                self.lightChannels == item.lightChannels and \
                                self.srt0 == item.srt0 and \
                                self.pat0 == item.pat0 and \
                                self.shader == item.shader and \
                                self.layers == item.layers)

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
        self.shaderStages = item.shaderStages
        self.indirectStages = item.indirectStages
        self.cullmode = item.cullmode
        self.compareBeforeTexture = item.compareBeforeTexture
        self.lightset = item.lightset
        self.fogset = item.fogset
        self.ref0 = item.ref0
        self.ref1 = item.ref1
        self.comp0 = item.comp0
        self.comp1 = item.comp1
        self.logic = item.logic
        self.depth_test = item.depth_test
        self.depth_update = item.depth_update
        self.depth_function = item.depth_function
        self.blend_enabled = item.blend_enabled
        self.blend_logic_enabled = item.blend_logic_enabled
        self.blend_dither = item.blend_dither
        self.blend_update_color = item.blend_update_color
        self.blend_update_alpha = item.blend_update_alpha
        self.blend_subtract = item.blend_subtract
        self.blend_logic = item.blend_logic
        self.blend_source = item.blend_source
        self.blend_dest = item.blend_dest
        self.constant_alpha_enabled = item.constant_alpha_enabled
        self.constant_alpha = item.constant_alpha
        self.colors = deepcopy(item.colors)
        self.constant_colors = deepcopy(item.constant_colors)
        self.ras1_ss = deepcopy(item.ras1_ss)
        self.indirect_matrices = deepcopy(item.indirect_matrices)
        self.lightChannels = deepcopy(item.lightChannels)

    def paste_layers(self, item):
        my_layers = self.layers
        item_layers = item.layers
        num_layers = len(item_layers)
        self.setLayerCount(num_layers)
        for i in range(num_layers):
            my_layer = my_layers[i]
            item_layer = item_layers[i]
            my_layer.paste(item_layer)
            my_layer.setName(item_layer.name)
            my_layer.tex0_ref = item_layer.get_tex0()
