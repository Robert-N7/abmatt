# Constants
from abmatt.autofix import AutoFix
from abmatt.brres.lib.matching import validBool, validInt, indexListItem, validFloat
from abmatt.brres.lib.node import Clipable

RASTER_LIGHT0 = 0
RASTER_LIGHT1 = 1
RASTER_BUMP_ALPHA = 4
RASTER_NORMALIZED_BUMP_ALPHA = 5
RASTER_ZERO = 6

CONSTANT_1_1 = 0
CONSTANT_7_8 = 1
CONSTANT_3_4 = 2
CONSTANT_5_8 = 3
CONSTANT_1_2 = 4
CONSTANT_3_8 = 5
CONSTANT_1_4 = 6
CONSTANT_1_8 = 7
CONSTANT_COLOR0_RGB = 12
CONSTANT_COLOR1_RGB = 13
CONSTANT_COLOR2_RGB = 14
CONSTANT_COLOR3_RGB = 15
CONSTANT_COLOR0_RRR = 16
CONSTANT_COLOR1_RRR = 17
CONSTANT_COLOR2_RRR = 18
CONSTANT_COLOR3_RRR = 19
CONSTANT_COLOR0_GGG = 20
CONSTANT_COLOR1_GGG = 21
CONSTANT_COLOR2_GGG = 22
CONSTANT_COLOR3_GGG = 23
CONSTANT_COLOR0_BBB = 24
CONSTANT_COLOR1_BBB = 25
CONSTANT_COLOR2_BBB = 26
CONSTANT_COLOR3_BBB = 27
CONSTANT_COLOR0_AAA = 28
CONSTANT_COLOR1_AAA = 29
CONSTANT_COLOR2_AAA = 30
CONSTANT_COLOR3_AAA = 31

COLOR_SEL_OUTPUT_COLOR = 0
COLOR_SEL_OUTPUT_ALPHA = 1
COLOR_SEL_COLOR0 = 2
COLOR_SEL_ALPHA0 = 3
COLOR_SEL_COLOR1 = 4
COLOR_SEL_ALPHA1 = 5
COLOR_SEL_COLOR2 = 6
COLOR_SEL_ALPHA2 = 7
COLOR_SEL_TEXTURE_COLOR = 8
COLOR_SEL_TEXTURE_ALPHA = 9
COLOR_SEL_RASTER_COLOR = 10
COLOR_SEL_RASTER_ALPHA = 11
COLOR_SEL_ONE = 12
COLOR_SEL_HALF = 13
COLOR_SEL_CONSTANT = 14
COLOR_SEL_NONE = 15

BIAS_ZERO = 0
BIAS_ADD_HALF = 1
BIAS_SUB_HALF = 2

OPER_ADD = 0
OPER_SUB = 1

SCALE_NONE = 0
SCALE_BY_TWO = 1
SCALE_BY_FOUR = 2
SCALE_BY_HALF = 3

DEST_OUTPUT = 0
DEST_COLOR0 = 1
DEST_COLOR1 = 2
DEST_COLOR2 = 3
DEST_ALPHA0 = 1
DEST_ALPHA1 = 2
DEST_ALPHA2 = 3

CONSTANT_ALPHA_COLOR0_RED = 16
CONSTANT_ALPHA_COLOR1_RED = 17
CONSTANT_ALPHA_COLOR2_RED = 18
CONSTANT_ALPHA_COLOR3_RED = 19
CONSTANT_ALPHA_COLOR0_GREEN = 20
CONSTANT_ALPHA_COLOR1_GREEN = 21
CONSTANT_ALPHA_COLOR2_GREEN = 22
CONSTANT_ALPHA_COLOR3_GREEN = 23
CONSTANT_ALPHA_COLOR0_BLUE = 24
CONSTANT_ALPHA_COLOR1_BLUE = 25
CONSTANT_ALPHA_COLOR2_BLUE = 26
CONSTANT_ALPHA_COLOR3_BLUE = 27
CONSTANT_ALPHA_COLOR0_ALPHA = 28
CONSTANT_ALPHA_COLOR1_ALPHA = 29
CONSTANT_ALPHA_COLOR2_ALPHA = 30
CONSTANT_ALPHA_COLOR3_ALPHA = 31

ALPHA_SEL_OUTPUT_ALPHA = 0
ALPHA_SEL_ALHPA0 = 1
ALPHA_SEL_ALHPA1 = 2
ALPHA_SEL_ALHPA2 = 3
ALPHA_SEL_TEXTURE_ALPHA = 4
ALPHA_SEL_RASTER_ALPHA = 5
ALPHA_SEL_CONSTANT = 6
ALPHA_SEL_NONE = 7

IND_BIAS_NONE = 0
IND_BIAS_S = 1
IND_BIAS_T = 2
IND_BIAS_ST = 3
IND_BIAS_U = 4
IND_BIAS_SU = 5
IND_BIAS_TU = 6
IND_BIAS_STU = 7

IND_MATRIX_NONE = 0
IND_MATRIX_0 = 1
IND_MATRIX_1 = 2
IND_MATRIX_2 = 3
IND_MATRIX_S0 = 5
IND_MATRIX_S1 = 6
IND_MATRIX_S2 = 7
IND_MATRIX_T0 = 9
IND_MATRIX_T1 = 10
IND_MATRIX_T2 = 11

IND_F_8_BIT_OFFSETS = 0
IND_F_5_BIT_OFFSETS = 1
IND_F_4_BIT_OFFSETS = 2
IND_F_3_BIT_OFFSETS = 3

IND_ALPHA_OFF = 0
IND_ALPHA_S = 1
IND_ALPHA_T = 2
IND_ALPHA_U = 3

IND_WRAP_NONE = 0
IND_WRAP_256 = 1
IND_WRAP_128 = 2
IND_WRAP_64 = 3
IND_WRAP_16 = 4
IND_WRAP_0 = 5
SCALEN = (1, 2, 4, 1 / 2)

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
              "colorselection", "zero")
BIAS = ("zero", "addhalf", "subhalf")
OPER = ("add", "subtract")
SCALE = ("multiplyby1", "multiplyby2", "multiplyby4", "divideby2")
COLOR_DEST = ("outputcolor", "color0", "color1", "color2")

# ALPHA
ALPHA_CONSTANTS = ("1_1", "7_8", "3_4", "5_8", "1_2", "3_8", "1_4", "1_8",
                   "color0_red", "color1_red", "color2_red", "color3_red",
                   "color0_green", "color1_green", "color2_green", "color3_green",
                   "color0_blue", "color1_blue", "color2_blue", "color3_blue",
                   "color0_alpha", "color1_alpha", "color2_alpha", "color3_alpha")
ALPHA_SELS = ("outputalpha", "alpha0", "alpha1", "alpha2", "texturealpha",
              "rasteralpha", "alphaselection", "zero")
ALPHA_DEST = ("outputalpha", "alpha0", "alpha1", "alpha2")

# INDIRECT TEVS
TEX_FORMAT = ("f_8_bit_offsets", "f_5_bit_offsets", "f_4_bit_offsets", "f_3_bit_offsets")
IND_BIAS = ("none", "s", "t", "st", "u", "su", "tu", "stu")
IND_ALPHA = ("off", "s", "t", "u")
IND_MATRIX = ("nomatrix", "matrix0", "matrix1", "matrix2", "matrixs0",
              "matrixs1", "matrixs2", "matrixt0", "matrixt1", "matrixt2")
WRAP = ("nowrap", "wrap256", "wrap128", "wrap64", "wrap16", "wrap0")


class Stage(Clipable):
    """ Single shader stage """
    REMOVE_UNUSED_LAYERS = False

    SETTINGS = ("enabled", "mapid", "coordinateid",
                "textureswapselection", "rastercolor",
                "rasterswapselection",
                "colorconstantselection", "constantcolorselection", "colora",
                "colorb", "colorc",
                "colord", "colorbias",
                "coloroperation", "colorclamp",
                "colorscale", "colordestination",
                "constantalphaselection", "alphaconstantselection", "alphaa",
                "alphab", "alphac",
                "alphad", "alphabias",
                "alphaoperation", "alphaclamp",
                "alphascale", "alphadestination",
                "indirectstage", "indirectformat",
                "indirectalpha",
                "indirectbias", "indirectmatrixselection",
                "indirectswrap", "indirecttwrap",
                "indirectuseprevstage", "indirectunmodifiedlod")

    def __init__(self, name, parent, binfile=None):
        super(Stage, self).__init__(name, parent, binfile)

    def __trace_color(self, sel):
        if sel != COLOR_SEL_NONE:
            if sel == COLOR_SEL_COLOR0:
                return 'color0'
            elif sel == COLOR_SEL_COLOR1:
                return 'color1'
            elif sel == COLOR_SEL_COLOR2:
                return 'color2'
            elif sel == COLOR_SEL_CONSTANT:
                return self.get_str('colorconstantselection')
            elif sel == COLOR_SEL_RASTER_COLOR:
                if self.raster_color == RASTER_LIGHT0 or self.raster_color == RASTER_LIGHT1:
                    return self.get_str('rastercolor')
        return None     # return nothing for anything else

    def get_colors_used(self, color_set):
        color_set.add(self.__trace_color(self.sel_a))
        color_set.add(self.__trace_color(self.sel_b))
        color_set.add(self.__trace_color(self.sel_c))
        color_set.add(self.__trace_color(self.sel_d))
        return color_set

    def __deepcopy__(self, memodict={}):
        ret = Stage(self.name, self.parent, False)
        ret.__copy_data_from(self)
        return ret

    def begin(self):
        self.enabled = True
        self.map_id = 0
        self.coord_id = 0
        self.texture_swap_sel = 0
        self.raster_color = RASTER_LIGHT0
        self.raster_swap_sel = 0
        # colors
        self.constant = CONSTANT_COLOR0_RGB
        self.sel_a = COLOR_SEL_NONE
        self.sel_b = COLOR_SEL_TEXTURE_COLOR
        self.sel_c = COLOR_SEL_RASTER_COLOR
        self.sel_d = COLOR_SEL_NONE
        self.bias = BIAS_ZERO
        self.oper = OPER_ADD
        self.clamp = True
        self.scale = SCALE_NONE
        self.dest = DEST_OUTPUT
        # alphas
        self.constant_a = CONSTANT_ALPHA_COLOR0_ALPHA
        self.sel_a_a = ALPHA_SEL_NONE
        self.sel_b_a = ALPHA_SEL_TEXTURE_ALPHA
        self.sel_c_a = ALPHA_SEL_RASTER_ALPHA
        self.sel_d_a = ALPHA_SEL_NONE
        self.bias_a = BIAS_ZERO
        self.oper_a = OPER_ADD
        self.clamp_a = True
        self.scale_a = SCALE_NONE
        self.dest_a = DEST_OUTPUT
        # indirect
        self.ind_stage = 0
        self.ind_format = IND_F_8_BIT_OFFSETS
        self.ind_alpha = IND_ALPHA_OFF
        self.ind_bias = IND_BIAS_NONE
        self.ind_matrix = IND_MATRIX_NONE
        self.ind_s_wrap = IND_WRAP_NONE
        self.ind_t_wrap = IND_WRAP_NONE
        self.ind_use_prev = False
        self.ind_unmodify_lod = False

    def __eq__(self, stage):
        """Determines if stages are equal"""
        return self.enabled == stage.enabled and \
               self.map_id == stage.map_id and \
               self.coord_id == stage.coord_id and \
               self.texture_swap_sel == stage.texture_swap_sel and \
               self.raster_color == stage.raster_color and \
               self.raster_swap_sel == stage.raster_swap_sel and \
               self.constant == stage.constant and \
               self.sel_a == stage.sel_a and \
               self.sel_b == stage.sel_b and \
               self.sel_c == stage.sel_c and \
               self.sel_d == stage.sel_d and \
               self.bias == stage.bias and \
               self.oper == stage.oper and \
               self.clamp == stage.clamp and \
               self.scale == stage.scale and \
               self.dest == stage.dest and \
               self.constant_a == stage.constant_a and \
               self.sel_a_a == stage.sel_a_a and \
               self.sel_b_a == stage.sel_b_a and \
               self.sel_c_a == stage.sel_c_a and \
               self.sel_d_a == stage.sel_d_a and \
               self.bias_a == stage.bias_a and \
               self.oper_a == stage.oper_a and \
               self.clamp_a == stage.clamp_a and \
               self.scale_a == stage.scale_a and \
               self.dest_a == stage.dest_a and \
               self.ind_stage == stage.ind_stage and \
               self.ind_format == stage.ind_format and \
               self.ind_alpha == stage.ind_alpha and \
               self.ind_bias == stage.ind_bias and \
               self.ind_matrix == stage.ind_matrix and \
               self.ind_s_wrap == stage.ind_s_wrap and \
               self.ind_t_wrap == stage.ind_t_wrap and \
               self.ind_use_prev == stage.ind_use_prev and \
               self.ind_unmodify_lod == stage.ind_unmodify_lod

    def __getitem__(self, item):
        return self.get_str(item)

    def __setitem__(self, key, value):
        return self.set_str(key, value)

    def check(self):
        pass

    # -------------------- CLIPBOARD --------------------------------------------------
    def clip(self, clipboard):
        clipboard[self.parent.getMaterialName() + str(self.name)] = self

    def clip_find(self, clipboard):
        return clipboard[self.parent.getMaterialName() + str(self.name)]

    def __copy_data_from(self, stage):
        self.enabled = stage.enabled
        self.coord_id = stage.coord_id
        self.map_id = stage.map_id
        self.texture_swap_sel = stage.texture_swap_sel
        self.raster_color = stage.raster_color
        self.raster_swap_sel = stage.raster_swap_sel
        # colors
        self.constant = stage.constant
        self.sel_a = stage.sel_a
        self.sel_b = stage.sel_b
        self.sel_c = stage.sel_c
        self.sel_d = stage.sel_d
        self.bias = stage.bias
        self.oper = stage.oper
        self.clamp = stage.clamp
        self.scale = stage.scale
        self.dest = stage.dest
        # alphas
        self.constant_a = stage.constant_a
        self.sel_a_a = stage.sel_a_a
        self.sel_b_a = stage.sel_b_a
        self.sel_c_a = stage.sel_c_a
        self.sel_d_a = stage.sel_d_a
        self.bias_a = stage.bias_a
        self.oper_a = stage.oper_a
        self.clamp_a = stage.clamp_a
        self.scale_a = stage.scale_a
        self.dest_a = stage.dest_a
        # indirect
        self.ind_stage = stage.ind_stage
        self.ind_format = stage.ind_format
        self.ind_alpha = stage.ind_alpha
        self.ind_bias = stage.ind_bias
        self.ind_matrix = stage.ind_matrix
        self.ind_s_wrap = stage.ind_s_wrap
        self.ind_t_wrap = stage.ind_t_wrap
        self.ind_use_prev = stage.ind_use_prev
        self.ind_unmodify_lod = stage.ind_unmodify_lod

    def paste(self, stage):
        self.__copy_data_from(stage)
        self.mark_modified()

    def info(self, key=None, indentation_level=0):
        trace = '>' + '  ' * indentation_level if indentation_level else '>' + str(self.parent.getMaterialName())
        if key:
            AutoFix.get().info('{}->Stage:{}\t{}:{}'.format(trace, self.name, key, self[key]), 1)
        else:
            AutoFix.get().info('{}Stage:{}\tMapId:{} ColorScale:{}'.format(
                trace, self.name, self['mapid'], self['colorscale']), 1)

    # --------------------------------------------------------------------
    # GETTERS/SETTERS
    # --------------------------------------------------------------------

    def is_enabled(self):
        return self.enabled

    def set_enabled(self, enable):
        if self.enabled != enable:
            self.enabled = enable
            self.mark_modified()

    def get_map_id(self):
        return self.map_id

    def set_map_id(self, id):
        if self.map_id != id:
            self.map_id = id
            self.mark_modified()

    def get_coord_id(self):
        return self.coord_id

    def set_coord_id(self, id):
        if self.coord_id != id:
            self.coord_id = id
            self.mark_modified()

    def get_tex_swap_sel(self):
        return self.texture_swap_sel

    def set_tex_swap_sel(self, sel):
        if self.texture_swap_sel != sel:
            self.texture_swap_sel = sel
            self.mark_modified()

    def get_raster_swap_sel(self):
        return self.raster_swap_sel

    def set_raster_swap_sel(self, i):
        if self.raster_swap_sel != i:
            self.raster_swap_sel = i
            self.mark_modified()

    def get_raster_color(self):
        return self.raster_color

    def set_raster_color(self, i):
        if i != self.raster_color:
            self.raster_color = i
            self.mark_modified()

    def get_constant_color(self):
        return self.constant

    def set_constant_color(self, index):
        if index != self.constant:
            self.constant = index
            self.mark_modified()

    def get_color_a(self):
        return self.sel_a

    def set_color_a(self, i):
        if i != self.sel_a:
            self.sel_a = i
            self.mark_modified()

    def get_color_b(self):
        return self.sel_b

    def set_color_b(self, i):
        if i != self.sel_b:
            self.sel_b = i
            self.mark_modified()

    def get_color_c(self):
        return self.sel_c

    def set_color_c(self, i):
        if i != self.sel_c:
            self.sel_c = i
            self.mark_modified()

    def get_color_d(self):
        return self.sel_d

    def set_color_d(self, i):
        if i != self.sel_d:
            self.sel_d = i
            self.mark_modified()

    def get_color_bias(self):
        return self.bias

    def set_color_bias(self, i):
        if i != self.bias:
            self.bias = i
            self.mark_modified()

    def get_color_oper(self):
        return self.oper

    def set_color_oper(self, i):
        if self.oper != i:
            self.oper = i
            self.mark_modified()

    def get_color_clamp(self):
        return self.clamp

    def set_color_clamp(self, enabled):
        if self.clamp != enabled:
            self.clamp = enabled
            self.mark_modified()

    def get_color_scale(self):
        return self.scale

    def set_color_scale(self, i):
        if self.scale != i:
            self.scale = i
            self.mark_modified()

    def get_color_dest(self):
        return self.dest

    def set_color_dest(self, i):
        if self.dest != i:
            self.dest = i
            self.mark_modified()

    def get_constant_alpha(self):
        return self.constant_a

    def set_constant_alpha(self, i):
        if self.constant_a != i:
            self.constant_a = i
            self.mark_modified()

    def get_alpha_a(self):
        return self.sel_a_a

    def set_alpha_a(self, i):
        if i != self.sel_a_a:
            self.sel_a_a = i
            self.mark_modified()

    def get_alpha_b(self):
        return self.sel_b_a

    def set_alpha_b(self, i):
        if i != self.sel_b_a:
            self.sel_b_a = i
            self.mark_modified()

    def get_alpha_c(self):
        return self.sel_c_a

    def set_alpha_c(self, i):
        if i != self.sel_c_a:
            self.sel_c_a = i
            self.mark_modified()

    def get_alpha_d(self):
        return self.sel_d_a

    def set_alpha_d(self, i):
        if i != self.sel_d_a:
            self.sel_d_a = i
            self.mark_modified()

    def get_alpha_bias(self):
        return self.bias_a

    def set_alpha_bias(self, i):
        if i != self.bias_a:
            self.bias_a = i
            self.mark_modified()

    def get_alpha_oper(self):
        return self.oper_a

    def set_alpha_oper(self, i):
        if self.oper_a != i:
            self.oper_a = i
            self.mark_modified()

    def get_alpha_clamp(self):
        return self.clamp_a

    def set_alpha_clamp(self, enabled):
        if self.clamp_a != enabled:
            self.clamp_a = enabled
            self.mark_modified()

    def get_alpha_scale(self):
        return self.scale_a

    def set_alpha_scale(self, i):
        if self.scale_a != i:
            self.scale_a = i
            self.mark_modified()

    def get_alpha_dest(self):
        return self.dest_a

    def set_alpha_dest(self, i):
        if self.dest_a != i:
            self.dest_a = i
            self.mark_modified()

    def get_ind_stage(self):
        return self.ind_stage

    def set_ind_stage(self, i):
        if self.ind_stage != i:
            self.ind_stage = i
            self.mark_modified()

    def get_ind_format(self):
        return self.ind_format

    def set_ind_format(self, i):
        if self.ind_format != i:
            self.ind_format = i
            self.mark_modified()

    def get_ind_alpha(self):
        return self.ind_alpha

    def set_ind_alpha(self, i):
        if self.ind_alpha != i:
            self.ind_alpha = i
            self.mark_modified()

    def get_ind_bias(self):
        return self.ind_bias

    def set_ind_bias(self, i):
        if self.ind_bias != i:
            self.ind_bias = i
            self.mark_modified()

    def get_ind_matrix(self):
        return self.ind_matrix

    def set_ind_matrix(self, i):
        if i != self.ind_matrix:
            self.ind_matrix = i
            self.mark_modified()

    def get_s_wrap(self):
        return self.ind_s_wrap

    def set_s_wrap(self, i):
        if self.ind_s_wrap != i:
            self.ind_s_wrap = i
            self.mark_modified()

    def get_t_wrap(self):
        return self.ind_t_wrap

    def set_t_wrap(self, i):
        if self.ind_t_wrap != i:
            self.ind_t_wrap = i
            self.mark_modified()

    def get_ind_use_prev(self):
        return self.ind_use_prev

    def set_ind_use_prev(self, enabled):
        if self.ind_use_prev != enabled:
            self.ind_use_prev = enabled
            self.mark_modified()

    def get_ind_unmodified_lod(self):
        return self.ind_unmodify_lod

    def set_ind_unmodified_lod(self, enabled):
        if self.ind_unmodify_lod != enabled:
            self.ind_unmodify_lod = enabled
            self.mark_modified()

    def set_str(self, key, value):
        s = self.SETTINGS
        if key == s[0]:
            self.set_enabled(validBool(value))
        elif key == s[1]:
            self.set_map_id(validInt(value, 0, 7))
        elif key == s[2]:
            self.set_coord_id(validInt(value, 0, 7))
        elif key == s[3]:
            self.set_tex_swap_sel(validInt(value, 0, 4))
        elif key == s[4]:
            if value == '0':
                self.set_raster_color(RASTER_ZERO)
            else:
                i = indexListItem(RASTER_COLORS, value)
                if i > 1:
                    i += 3
                self.set_raster_color(i)
        elif key == s[5]:
            self.set_raster_swap_sel(validInt(value, 0, 4))
        elif key in s[6:8]:
            value = value.replace('constant', '')
            i = indexListItem(COLOR_CONSTANTS, value)
            if i > 7:
                i += 4
            self.set_constant_color(i)
        elif key in s[8:12]:
            if value == '0':
                val = COLOR_SEL_NONE
            elif value == '1':
                val = COLOR_SEL_ONE
            elif value in ('0.5', '1/2'):
                val = COLOR_SEL_HALF
            else:
                val = indexListItem(COLOR_SELS, value)
            if key == s[8]:
                self.set_color_a(val)
            elif key == s[9]:
                self.set_color_b(val)
            elif key == s[10]:
                self.set_color_c(val)
            elif key == s[11]:
                self.set_color_d(val)
        elif key == s[12]:
            self.set_color_bias(indexListItem(BIAS, value))
        elif key == s[13]:
            self.set_color_oper(indexListItem(OPER, value))
        elif key == s[14]:
            self.set_color_clamp(validBool(value))
        elif key in (s[15], s[26]):
            try:
                val = indexListItem(SCALE, value)
            except ValueError:
                f = validFloat(value, 0.5, 4)
                val = indexListItem(SCALEN, f)
            if key == s[15]:
                self.set_color_scale(val)
            elif key == s[26]:
                self.set_alpha_scale(val)
        elif key == s[16]:
            self.set_color_dest(indexListItem(COLOR_DEST, value))
        elif key in s[17:19]:
            value = value.replace('constant', '')
            i = indexListItem(ALPHA_CONSTANTS, value)
            if i > 7:
                i += 8
            self.set_constant_alpha(i)
        elif key in s[19:23]:
            if value == '0':
                val = ALPHA_SEL_NONE
            else:
                val = indexListItem(ALPHA_SELS, value)
            if key == s[19]:
                self.set_alpha_a(val)
            elif key == s[20]:
                self.set_alpha_b(val)
            elif key == s[21]:
                self.set_alpha_c(val)
            elif key == s[22]:
                self.set_alpha_d(val)
        elif key == s[23]:
            self.set_alpha_bias(indexListItem(BIAS, value))
        elif key == s[24]:
            self.set_alpha_oper(indexListItem(OPER, value))
        elif key == s[25]:
            self.set_alpha_clamp(validBool(value))
        elif key == s[27]:
            self.set_alpha_dest(indexListItem(ALPHA_DEST, value))
        elif key == s[28]:
            self.set_ind_stage(validInt(value, 0, 4))
        elif key == s[29]:
            self.set_ind_format(indexListItem(TEX_FORMAT, value))
        elif key == s[30]:
            self.set_ind_alpha(indexListItem(IND_ALPHA, value))
        elif key == s[31]:
            self.set_ind_bias(indexListItem(IND_BIAS, value))
        elif key == s[32]:
            if len(value) < 6:
                value = 'matrix' + value
            i = indexListItem(IND_MATRIX, value)
            if i > 3:
                i += 1
            if i > 7:
                i += 1
            self.set_ind_matrix(i)
        elif key == s[33]:
            self.set_s_wrap(indexListItem(WRAP, value))
        elif key == s[34]:
            self.set_t_wrap(indexListItem(WRAP, value))
        elif key == s[35]:
            self.set_ind_use_prev(validBool(value))
        elif key == s[36]:
            self.set_ind_unmodified_lod(validBool(value))

    def get_str(self, key):
        s = self.SETTINGS
        if key == s[0]:
            return self.enabled
        elif key == s[1]:
            return self.map_id
        elif key == s[2]:
            return self.coord_id
        elif key == s[3]:
            return self.texture_swap_sel
        elif key == s[4]:
            x = self.raster_color
            if x > 1:
                x -= 3
            return RASTER_COLORS[x]
        elif key == s[5]:
            return self.raster_swap_sel
        elif key in s[6:8]:
            x = self.constant
            if x > 7:
                x += 4
            return COLOR_CONSTANTS[x]
        elif key == s[8]:
            return COLOR_SELS[self.sel_a]
        elif key == s[9]:
            return COLOR_SELS[self.sel_b]
        elif key == s[10]:
            return COLOR_SELS[self.sel_c]
        elif key == s[11]:
            return COLOR_SELS[self.sel_d]
        elif key == s[12]:
            return BIAS[self.bias]
        elif key == s[13]:
            return OPER[self.oper]
        elif key == s[14]:
            return self.clamp
        elif key == s[15]:
            return SCALE[self.scale]
        elif key == s[16]:
            return COLOR_DEST[self.dest]
        elif key in s[17:19]:
            x = self.constant_a
            if x > 7:
                x -= 8
            return ALPHA_CONSTANTS[x]
        elif key == s[19]:
            return ALPHA_SELS[self.sel_a_a]
        elif key == s[20]:
            return ALPHA_SELS[self.sel_b_a]
        elif key == s[21]:
            return ALPHA_SELS[self.sel_c_a]
        elif key == s[22]:
            return ALPHA_SELS[self.sel_d_a]
        elif key == s[23]:
            return BIAS[self.bias_a]
        elif key == s[24]:
            return OPER[self.oper_a]
        elif key == s[25]:
            return self.clamp_a
        elif key == s[26]:
            return SCALE[self.scale_a]
        elif key == s[27]:
            return ALPHA_DEST[self.dest_a]
        elif key == s[28]:
            return self.ind_stage
        elif key == s[29]:
            return TEX_FORMAT[self.ind_format]
        elif key == s[30]:
            return IND_ALPHA[self.ind_alpha]
        elif key == s[31]:
            return IND_BIAS[self.ind_bias]
        elif key == s[32]:
            x = self.ind_matrix
            if x > 8:
                x -= 1
            if x > 4:
                x -= 1
            return IND_MATRIX[x]
        elif key == s[33]:
            return WRAP[self.ind_s_wrap]
        elif key == s[34]:
            return WRAP[self.ind_t_wrap]
        elif key == s[35]:
            return self.ind_use_prev
        elif key == s[36]:
            return self.ind_unmodify_lod
