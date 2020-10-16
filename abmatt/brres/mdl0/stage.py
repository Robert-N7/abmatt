
# Constants
from brres.lib.node import Clipable

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


class Stage(Clipable):
    """ Single shader stage """
    REMOVE_UNUSED_LAYERS = False
    SCALEN = (1, 2, 4, 1 / 2)

    # INDIRECT TEVS
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

    def __deepcopy__(self, memodict={}):
        ret = Stage(self.name, self.parent, False)
        ret.paste(self)
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

    def get_str(self, key):
        raise NotImplementedError()
        i = key.find('constant')
        if 0 <= i < 5:  # out of order
            is_alpha = True if 'alpha' in key else False
            if is_alpha:
                key = 'alphaconstantselection'
            else:
                key = 'colorconstantselection'
        # todo fix this hot mess
        if key not in self.map:
            raise ValueError("Invalid setting {} possible keys are: \n\t{}".format(key, self.SETTINGS))
        return self.map[key]

    def check(self):
        pass

    # -------------------- CLIPBOARD --------------------------------------------------
    def clip(self, clipboard):
        clipboard[self.parent.getMaterialName() + str(self.name)] = self

    def clip_find(self, clipboard):
        return clipboard[self.parent.getMaterialName() + str(self.name)]

    def paste(self, stage):
        # ignores name and parent, since it's shader's job to track names
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
        self.mark_modified()

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level if indentation_level else '>' + str(self.parent.getMaterialName())
        if key:
            print('{}->Stage:{}\t{}:{}'.format(trace, self.name, key, self[key]))
        else:
            print('{}Stage:{}\tMapId:{} ColorScale:{}'.format(
                trace, self.name, self['mapid'], self['colorscale']))

    def getRasterColorI(self):
        return self.raster_color

    def setRasterColorI(self, i):
        if i != self.raster_color:
            self.raster_color = i
            self.mark_modified()

    def getConstantAlphaI(self):
        return self.constant_a

    def setConstantAlphaI(self, i):
        if self.constant_a != i:
            self.constant_a = i
            self.mark_modified()

    def getIndMtxI(self):
        return self.ind_matrix

    def setIndTexMtxI(self, i):
        if i != self.ind_matrix:
            self.ind_matrix = i
            self.mark_modified()

    def getConstantColorI(self):
        return self.constant

    def setConstantColorI(self, index):
        if index != self.constant:
            self.constant = index
            self.mark_modified()

    def set_str(self, key, value):
        # todo fix this hot mess
        raise NotImplementedError()
        i = key.find('constant')
        is_alpha = True if 'alpha' in key else False
        if 0 <= i < 5:  # out of order
            if is_alpha:
                key = 'alphaconstantselection'
            else:
                key = 'colorconstantselection'
        if not key in self.map:
            raise ValueError("No such shader stage setting {} possible keys are: \n\t{}".format(key, self.map.keys()))
        # bools
        if key == "enabled" or "clamp" in key or key == "indirectuseprevstage" \
                or key == "indirectunmodifiedlod":
            b = validBool(value)
            if self.map[key] != b:
                self.map[key] = b
        # ints
        elif "swap" in key or "stage" in key:
            i = validInt(value, 0, 4)
            if i != self.map[key]:
                self.map[key] = i
                self.mark_modified()
        elif "id" in key:
            i = validInt(value, 0, 7)
            if self.map[key] != i:
                self.map[key] = i
                self.mark_modified()
        else:  # list indexing ones
            value = value.replace('constant', '')
            if "scale" in key:
                try:
                    f = validFloat(value, 0.5, 4)
                    pos = indexListItem(self.SCALEN, f)
                    if value != self.SCALE[pos]:
                        value = self.SCALE[pos]
                        self.mark_modified()
                except ValueError:
                    indexListItem(self.SCALE, value)
            elif "color" in key:
                if len(key) < 7:  # abcd
                    if value == '0':
                        value = 'zero'
                    elif value == '1':
                        value = 'one'
                    elif value == '0.5':
                        value = 'half'
                    else:
                        indexListItem(self.COLOR_SELS, value)
                elif key == "colorconstantselection":
                    value = value.replace('constant', '')
                    indexListItem(self.COLOR_CONSTANTS, value)
                elif key == "colordestination":
                    indexListItem(self.COLOR_DEST, value)
                elif key == "colorbias":
                    indexListItem(self.BIAS, value)
                elif key == "coloroperation":
                    indexListItem(self.OPER, value)
                elif key == "rastercolor":
                    if value == '0':
                        value = 'zero'
                    else:
                        indexListItem(self.RASTER_COLORS, value)
            elif is_alpha:
                if len(key) < 7:  # abcd
                    if value == '0':
                        value = 'zero'
                    else:
                        indexListItem(self.ALPHA_SELS, value)
                elif key == "alphaconstantselection":
                    value = value.replace('constant', '')
                    indexListItem(self.ALPHA_CONSTANTS, value)
                elif key == "alphadestination":
                    indexListItem(self.ALPHA_DEST, value)
                elif key == "alphabias":
                    indexListItem(self.BIAS, value)
                elif key == "alphaoperation":
                    indexListItem(self.OPER, value)
            elif "indirect" in key:
                if key == "indirectformat":
                    indexListItem(self.TEX_FORMAT, value)
                elif key == "indirectmatrixselection":
                    if len(value) < 6:
                        value = 'matrix' + value
                    indexListItem(self.IND_MATRIX, value)
                elif key == "indirectalpha":
                    indexListItem(self.IND_ALPHA, value)
                elif key == "indirectbias":
                    indexListItem(self.IND_BIAS, value)
                elif "wrap" in key:
                    indexListItem(self.WRAP, value)
            if self.map[key] != value:
                self.map[key] = value
                self.mark_modified()

    def unpackColorEnv(self, binfile):
        """ Unpacks the color env """
        ce = ColorEnv(self.name)
        ce.unpack(binfile)
        self.map["colora"] = self.COLOR_SELS[ce.getSelA()]
        self.map["colorb"] = self.COLOR_SELS[ce.getSelB()]
        self.map["colorc"] = self.COLOR_SELS[ce.getSelC()]
        self.map["colord"] = self.COLOR_SELS[ce.getSelD()]
        self.map["colorbias"] = self.BIAS[ce.getBias()]
        self.map["coloroperation"] = self.OPER[ce.getSub()]
        self.map["colorclamp"] = ce.getClamp()
        self.map["colorscale"] = self.SCALE[ce.getShift()]
        self.map["colordestination"] = self.COLOR_DEST[ce.getDest()]

    def unpackAlphaEnv(self, binfile):
        """ Unpacks alpha env """
        ae = AlphaEnv(self.name)
        ae.unpack(binfile)
        self.map["alphaa"] = self.ALPHA_SELS[ae.getSelA()]
        self.map["alphab"] = self.ALPHA_SELS[ae.getSelB()]
        self.map["alphac"] = self.ALPHA_SELS[ae.getSelC()]
        self.map["alphad"] = self.ALPHA_SELS[ae.getSelD()]
        self.map["alphabias"] = self.BIAS[ae.getBias()]
        self.map["alphaoperation"] = self.OPER[ae.getSub()]
        self.map["alphaclamp"] = ae.getClamp()
        self.map["alphascale"] = self.SCALE[ae.getShift()]
        self.map["alphadestination"] = self.ALPHA_DEST[ae.getDest()]
        self.map["textureswapselection"] = ae.getTSwap()
        self.map["rasterswapselection"] = ae.getRSwap()

    def unpackIndirect(self, binfile):
        c = IndCmd(self.name)
        c.unpack(binfile)
        self.map["indirectstage"] = c.getStage()
        self.map["indirectformat"] = self.TEX_FORMAT[c.getFormat()]
        self.map["indirectbias"] = self.IND_BIAS[c.getBias()]
        self.setIndTexMtxI(c.getMtx(), False)
        self.map["indirectswrap"] = self.WRAP[c.getSWrap()]
        self.map["indirecttwrap"] = self.WRAP[c.getTWrap()]
        self.map["indirectalpha"] = self.IND_ALPHA[c.getAlpha()]
        self.map["indirectuseprevstage"] = c.getUsePrevStage()
        self.map["indirectunmodifiedlod"] = c.getUnmodifiedLOD()

    def packColorEnv(self, binfile):
        ce = ColorEnv(self.name)
        a = self.COLOR_SELS.index(self["colora"])
        b = self.COLOR_SELS.index(self["colorb"])
        c = self.COLOR_SELS.index(self["colorc"])
        d = self.COLOR_SELS.index(self["colord"])
        bi = self.BIAS.index(self["colorbias"])
        op = self.OPER.index(self["coloroperation"])
        sc = self.SCALE.index(self["colorscale"])
        dest = self.COLOR_DEST.index(self["colordestination"])
        ce.data = dest << 22 | sc << 20 | self["colorclamp"] << 19 | op << 18 \
                  | bi << 16 | a << 12 | b << 8 | c << 4 | d
        ce.pack(binfile)

    def packAlphaEnv(self, binfile):
        ae = AlphaEnv(self.name)
        a = self.ALPHA_SELS.index(self["alphaa"])
        b = self.ALPHA_SELS.index(self["alphab"])
        c = self.ALPHA_SELS.index(self["alphac"])
        d = self.ALPHA_SELS.index(self["alphad"])
        bi = self.BIAS.index(self["alphabias"])
        op = self.OPER.index(self["alphaoperation"])
        sc = self.SCALE.index(self["alphascale"])
        dest = self.ALPHA_DEST.index(self["alphadestination"])
        ae.data = dest << 22 | sc << 20 | self["alphaclamp"] << 19 | op << 18 \
                  | bi << 16 | a << 13 | b << 10 | c << 7 | d << 4 \
                  | self["textureswapselection"] << 2 | self["rasterswapselection"]
        ae.pack(binfile)

    def packIndirect(self, binfile):
        c = IndCmd(self.name)
        f = self.TEX_FORMAT.index(self["indirectformat"])
        b = self.IND_BIAS.index(self["indirectbias"])
        a = self.IND_ALPHA.index(self["indirectalpha"])
        m = self.getIndMtxI()
        sw = self.WRAP.index(self["indirectswrap"])
        tw = self.WRAP.index(self["indirecttwrap"])
        c.data = self["indirectunmodifiedlod"] << 20 | self["indirectuseprevstage"] << 19 \
                 | tw << 16 | sw << 13 | m << 9 | a << 7 | b << 4 | f << 2 \
                 | self["indirectstage"]
        c.pack(binfile)

