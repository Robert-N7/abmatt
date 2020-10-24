from abmatt.brres.lib.packing.interface import Packer


def pack_ras1_ss(binfile, data, index):
    pack_bp(binfile, BPMEM_RAS1_SS0 + index, data)


def pack_ras1_iref(binfile, ind_maps, ind_coords):
    data = 0
    for i in range(3, -1, -1):
        data <<= 3
        data |= ind_coords[i] & 7
        data <<= 3
        data |= ind_maps[i] & 7
    pack_bp(binfile, BPMEM_IREF, data)


def pack_ind_cmd(binfile, index, stage, format, bias, alpha,
                 matrix, swrap, twrap,
                 use_prev_stage, unmodifiedLOD):
    data = stage & 3 | (format & 3) << 2 | (bias & 7) << 4 | (alpha & 3) << 7 \
           | (matrix & 7) << 9 | (swrap & 7) << 13 | (twrap & 7) << 16 \
           | (use_prev_stage & 1) << 19 | (unmodifiedLOD & 1) << 20
    pack_bp(binfile, BPMEM_IND_CMD0 + index, data)


def pack_alpha_env(binfile, index, a, b, c, d,
                   dest, bias, op, clamp, shift,
                   tswap, rswap):
    data = (a & 7) << 13 | (b & 7) << 10 | (c & 7) << 7 | (d & 7) << 4 \
           | (dest & 3) << 22 | (bias & 3) << 16 | (op & 1) << 18 | (clamp & 1) << 19 | (shift & 3) << 20 \
           | (tswap & 3) << 2 | rswap & 3
    pack_bp(binfile, BPMEM_TEV_ALPHA_ENV_0 + (index * 2), data)


def pack_color_env(binfile, index, a, b, c, d,
                   dest, bias, op,
                   clamp, shift):
    data = (a & 0xf) << 12 | (b & 0xf) << 8 | (c & 0xf) << 4 | (d & 0xf) \
           | (dest & 3) << 22 | (bias & 3) << 16 | (op & 1) << 18 \
           | (clamp & 1) << 19 | (shift & 3) << 20
    pack_bp(binfile, BPMEM_TEV_COLOR_ENV_0 + (index * 2), data)


def pack_tref_helper(map, coord, enable, raster):
    return map & 7 | (coord & 7) << 3 | (enable & 1) << 6 | (raster & 7) << 7


def pack_tref(binfile, index, map0, coord0, enable0, raster0,
              map1=None, coord1=None, enable1=None, raster1=None):
    data = pack_tref_helper(map0, coord0, enable0, raster0)
    if map1 is not None:
        data |= pack_tref_helper(map1, coord1, enable1, raster1) << 12
    pack_bp(binfile, BPMEM_TREF0 + index, data)


def pack_kcel(binfile, index,
              csel0, csel_a0, csel1=0, csel_a1=0,
              xga0=0, xrgb0=0):
    data = (csel0 & 0x1f) << 4 | (csel_a0 & 0x1f) << 9 | (csel1 & 0x1f) << 14 \
           | (csel_a1 & 0x1f) << 19 | (xga0 & 3) << 2 | xrgb0 & 3
    pack_bp(binfile, BPMEM_TEV_KSEL0 + index, data)


def pack_bp_mask(binfile, mask=0):
    pack_bp(binfile, BPMEM_BP_MASK, mask)


def pack_alpha_function(binfile, ref0, ref1, comp0, comp1, logic):
    data = ref0 & 0xff | (ref1 & 0xff) << 8 | (comp0 & 7) << 16 | (comp1 & 7) << 19 | (logic & 3) << 22
    pack_bp(binfile, BPMEM_ALPHACOMPARE, data)


def pack_zmode(binfile, depth_test, depth_update, depth_function):
    data = depth_test & 1 | (depth_update & 1) << 4 | (depth_function & 7) << 1
    pack_bp(binfile, BPMEM_ZMODE, data)


def pack_blend_mode(binfile, enabled, logic_enabled, dither,
                    color, alpha, subtract, logic,
                    source, dest):
    data = enabled & 1 | (logic_enabled & 1) << 1 | (dither & 1) << 2 \
           | (color & 1) << 3 | (alpha & 1) << 4 | (subtract & 1) << 11 | (logic & 0xf) << 12 \
           | (source & 7) << 8 | (dest & 7) << 5
    pack_bp(binfile, BPMEM_BLENDMODE, data)


def pack_constant_alpha(binfile, enabled, alpha):
    data = (enabled & 1) << 8 | alpha & 0xff
    pack_bp(binfile, BPMEM_CONSTANTALPHA, data)


class PackIndMtx(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def encode11bitFloat(self, val):
        """Encodes the 10bit float as int
            100 0000 0000 sign
            011 1111 1111 mantissa
        """
        e = 1 if val < 0 else 0  # sign
        start = 2
        bitn = 1
        val = abs(val)
        while bitn <= 10:
            e <<= 1  # make room
            subtractee = 1 / start  # divide by exponent of 2
            if val >= subtractee:  # can subtractee be taken out?
                val -= subtractee
                e |= 1  # then place a bit
            bitn += 1  # increase the number of bits
            start <<= 1
        return e

    def pack(self, matrix, binfile):
        """Packs the ind matrix """
        if not matrix.enabled:
            binfile.advance(15)
            return
        bpmem = BPMEM_IND_MTXA0 + self.index * 3
        scale = matrix.scale + 17
        for i in range(3):
            sbits = (scale >> (2 * i) & 3)
            r0 = self.encode11bitFloat(matrix.matrix[0][i])
            r1 = self.encode11bitFloat(matrix.matrix[1][i])
            data = sbits << 22 | r1 << 11 | r0
            pack_bp(binfile, bpmem, data)
            bpmem += 1


def pack_color(binfile, index, color, is_constant):
    bpmem = BPMEM_TEV_REGISTER_L_0 + (2 * index)
    pack_color_reg(binfile, bpmem, color[3], color[0])
    bpmem += 1
    green = color[1]
    blue = color[2]
    pack_color_reg(binfile, bpmem, green, blue)
    if not is_constant:
        pack_color_reg(binfile, bpmem, green, blue)
        pack_color_reg(binfile, bpmem, green, blue)


def pack_color_reg(binfile, bpmem, left_bits, right_bits):
    data = (left_bits & 0x7ff) << 12 | right_bits & 0xfff
    pack_bp(binfile, bpmem, data)


def pack_bp(binfile, bp_mem, data):
    binfile.write('BI', LOAD_BP, bp_mem << 24 | data & 0xffffff)


# Constants
# BPMEM_GENMODE = 0x00

# BPMEM_DISPLAYCOPYFILER0 = 0x01
# BPMEM_DISPLAYCOPYFILER1 = 0x02
# BPMEM_DISPLAYCOPYFILER2 = 0x03
# BPMEM_DISPLAYCOPYFILER3 = 0x04
# BPMEM_DISPLAYCOPYFILER4 = 0x05
LOAD_BP = 0x61

BPMEM_IND_MTXA0 = 0x06
# BPMEM_IND_MTXB0 = 0x07
# BPMEM_IND_MTXC0 = 0x08
# BPMEM_IND_MTXA1 = 0x09
# BPMEM_IND_MTXB1 = 0x0A
# BPMEM_IND_MTXC1 = 0x0B
# BPMEM_IND_MTXA2 = 0x0C
# BPMEM_IND_MTXB2 = 0x0D
# BPMEM_IND_MTXC2 = 0x0E
# BPMEM_IND_IMASK = 0x0F

BPMEM_IND_CMD0 = 0x10
# BPMEM_IND_CMD1 = 0x11
# BPMEM_IND_CMD2 = 0x12
# BPMEM_IND_CMD3 = 0x13
# BPMEM_IND_CMD4 = 0x14
# BPMEM_IND_CMD5 = 0x15
# BPMEM_IND_CMD6 = 0x16
# BPMEM_IND_CMD7 = 0x17
# BPMEM_IND_CMD8 = 0x18
# BPMEM_IND_CMD9 = 0x19
# BPMEM_IND_CMDA = 0x1A
# BPMEM_IND_CMDB = 0x1B
# BPMEM_IND_CMDC = 0x1C
# BPMEM_IND_CMDD = 0x1D
# BPMEM_IND_CMDE = 0x1E
# BPMEM_IND_CMDF = 0x1F

# BPMEM_SCISSORTL = 0x20
# BPMEM_SCISSORBR = 0x21
# BPMEM_LINEPTWIDTH = 0x22
# BPMEM_PERF0_TRI = 0x23
# BPMEM_PERF0_QUAD = 0x24

BPMEM_RAS1_SS0 = 0x25
BPMEM_RAS1_SS1 = 0x26
BPMEM_IREF = 0x27

BPMEM_TREF0 = 0x28
# BPMEM_TREF1 = 0x29
# BPMEM_TREF2 = 0x2A
# BPMEM_TREF3 = 0x2B
# BPMEM_TREF4 = 0x2C
# BPMEM_TREF5 = 0x2D
# BPMEM_TREF6 = 0x2E
# BPMEM_TREF7 = 0x2F

# BPMEM_SU_SSIZE0 = 0x30
# BPMEM_SU_TSIZE0 = 0x31
# BPMEM_SU_SSIZE1 = 0x32
# BPMEM_SU_TSIZE1 = 0x33
# BPMEM_SU_SSIZE2 = 0x34
# BPMEM_SU_TSIZE2 = 0x35
# BPMEM_SU_SSIZE3 = 0x36
# BPMEM_SU_TSIZE3 = 0x37
# BPMEM_SU_SSIZE4 = 0x38
# BPMEM_SU_TSIZE4 = 0x39
# BPMEM_SU_SSIZE5 = 0x3A
# BPMEM_SU_TSIZE5 = 0x3B
# BPMEM_SU_SSIZE6 = 0x3C
# BPMEM_SU_TSIZE6 = 0x3D
# BPMEM_SU_SSIZE7 = 0x3E
# BPMEM_SU_TSIZE7 = 0x3F

BPMEM_ZMODE = 0x40
BPMEM_BLENDMODE = 0x41
BPMEM_CONSTANTALPHA = 0x42
# BPMEM_ZCOMPARE = 0x43
# BPMEM_FIELDMASK = 0x44
# BPMEM_SETDRAWDONE = 0x45
# BPMEM_BUSCLOCK0 = 0x46
# BPMEM_PE_TOKEN_ID = 0x47
# BPMEM_PE_TOKEN_INT_ID = 0x48

# BPMEM_EFB_TL = 0x49
# BPMEM_EFB_BR = 0x4A
# BPMEM_EFB_ADDR = 0x4B

# BPMEM_MIPMAP_STRIDE = 0x4D
# BPMEM_COPYYSCALE = 0x4E
#
# BPMEM_CLEAR_AR = 0x4F
# BPMEM_CLEAR_GB = 0x50
# BPMEM_CLEAR_Z = 0x51

# BPMEM_TRIGGER_EFB_COPY = 0x52
# BPMEM_COPYFILTER0 = 0x53
# BPMEM_COPYFILTER1 = 0x54
# BPMEM_CLEARBBOX1 = 0x55
# BPMEM_CLEARBBOX2 = 0x56

# BPMEM_UNKNOWN_57 = 0x57

# BPMEM_REVBITS = 0x58
# BPMEM_SCISSOROFFSET = 0x59
#
# BPMEM_UNKNOWN_60 = 0x60
# BPMEM_UNKNOWN_61 = 0x61
# BPMEM_UNKNOWN_62 = 0x62

# BPMEM_TEXMODESYNC = 0x63
# BPMEM_LOADTLUT0 = 0x64
# BPMEM_LOADTLUT1 = 0x65
# BPMEM_TEXINVALIDATE = 0x66
# BPMEM_PERF1 = 0x67
# BPMEM_FIELDMODE = 0x68
# BPMEM_BUSCLOCK1 = 0x69

# BPMEM_TX_SETMODE0_A = 0x80
# BPMEM_TX_SETMODE0_B = 0x81
# BPMEM_TX_SETMODE0_C = 0x82
# BPMEM_TX_SETMODE0_D = 0x83
#
# BPMEM_TX_SETMODE1_A = 0x84
# BPMEM_TX_SETMODE1_B = 0x85
# BPMEM_TX_SETMODE1_C = 0x86
# BPMEM_TX_SETMODE1_D = 0x87
#
# BPMEM_TX_SETIMAGE0_A = 0x88
# BPMEM_TX_SETIMAGE0_B = 0x89
# BPMEM_TX_SETIMAGE0_C = 0x8A
# BPMEM_TX_SETIMAGE0_D = 0x8B
#
# BPMEM_TX_SETIMAGE1_A = 0x8C
# BPMEM_TX_SETIMAGE1_B = 0x8D
# BPMEM_TX_SETIMAGE1_C = 0x8E
# BPMEM_TX_SETIMAGE1_D = 0x8F
#
# BPMEM_TX_SETIMAGE2_A = 0x90
# BPMEM_TX_SETIMAGE2_B = 0x91
# BPMEM_TX_SETIMAGE2_C = 0x92
# BPMEM_TX_SETIMAGE2_D = 0x93
#
# BPMEM_TX_SETIMAGE3_A = 0x94
# BPMEM_TX_SETIMAGE3_B = 0x95
# BPMEM_TX_SETIMAGE3_C = 0x96
# BPMEM_TX_SETIMAGE3_D = 0x97
#
# BPMEM_TX_SETTLUT_A = 0x98
# BPMEM_TX_SETTLUT_B = 0x99
# BPMEM_TX_SETTLUT_C = 0x9A
# BPMEM_TX_SETTLUT_D = 0x9B
#
# BPMEM_TX_SETMODE0_4_A = 0xA0
# BPMEM_TX_SETMODE0_4_B = 0xA1
# BPMEM_TX_SETMODE0_4_C = 0xA2
# BPMEM_TX_SETMODE0_4_D = 0xA3
#
# BPMEM_TX_SETMODE1_4_A = 0xA4
# BPMEM_TX_SETMODE1_4_B = 0xA5
# BPMEM_TX_SETMODE1_4_C = 0xA6
# BPMEM_TX_SETMODE1_4_D = 0xA7
#
# BPMEM_TX_SETIMAGE0_4_A = 0xA8
# BPMEM_TX_SETIMAGE0_4_B = 0xA9
# BPMEM_TX_SETIMAGE0_4_C = 0xAA
# BPMEM_TX_SETIMAGE0_4_D = 0xAB
#
# BPMEM_TX_SETIMAGE1_4_A = 0xAC
# BPMEM_TX_SETIMAGE1_4_B = 0xAD
# BPMEM_TX_SETIMAGE1_4_C = 0xAE
# BPMEM_TX_SETIMAGE1_4_D = 0xAF
#
# BPMEM_TX_SETIMAGE2_4_A = 0xB0
# BPMEM_TX_SETIMAGE2_4_B = 0xB1
# BPMEM_TX_SETIMAGE2_4_C = 0xB2
# BPMEM_TX_SETIMAGE2_4_D = 0xB3
#
# BPMEM_TX_SETIMAGE3_4_A = 0xB4
# BPMEM_TX_SETIMAGE3_4_B = 0xB5
# BPMEM_TX_SETIMAGE3_4_C = 0xB6
# BPMEM_TX_SETIMAGE3_4_D = 0xB7

# BPMEM_TX_SETLUT_4_A = 0xB8
# BPMEM_TX_SETLUT_4_B = 0xB9
# BPMEM_TX_SETLUT_4_C = 0xBA
# BPMEM_TX_SETLUT_4_D = 0xBB
#
# BPMEM_UNKNOWN_BC = 0xBC
# BPMEM_UNKNOWN_BB = 0xBB
# BPMEM_UNKNOWN_BD = 0xBD
# BPMEM_UNKNOWN_BE = 0xBE
# BPMEM_UNKNOWN_BF = 0xBF

BPMEM_TEV_COLOR_ENV_0 = 0xC0
BPMEM_TEV_ALPHA_ENV_0 = 0xC1
# BPMEM_TEV_COLOR_ENV_1 = 0xC2
# BPMEM_TEV_ALPHA_ENV_1 = 0xC3
# BPMEM_TEV_COLOR_ENV_2 = 0xC4
# BPMEM_TEV_ALPHA_ENV_2 = 0xC5
# BPMEM_TEV_COLOR_ENV_3 = 0xC6
# BPMEM_TEV_ALPHA_ENV_3 = 0xC7
# BPMEM_TEV_COLOR_ENV_4 = 0xC8
# BPMEM_TEV_ALPHA_ENV_4 = 0xC9
# BPMEM_TEV_COLOR_ENV_5 = 0xCA
# BPMEM_TEV_ALPHA_ENV_5 = 0xCB
# BPMEM_TEV_COLOR_ENV_6 = 0xCC
# BPMEM_TEV_ALPHA_ENV_6 = 0xCD
# BPMEM_TEV_COLOR_ENV_7 = 0xCE
# BPMEM_TEV_ALPHA_ENV_7 = 0xCF
# BPMEM_TEV_COLOR_ENV_8 = 0xD0
# BPMEM_TEV_ALPHA_ENV_8 = 0xD1
# BPMEM_TEV_COLOR_ENV_9 = 0xD2
# BPMEM_TEV_ALPHA_ENV_9 = 0xD3
# BPMEM_TEV_COLOR_ENV_A = 0xD4
# BPMEM_TEV_ALPHA_ENV_A = 0xD5
# BPMEM_TEV_COLOR_ENV_B = 0xD6
# BPMEM_TEV_ALPHA_ENV_B = 0xD7
# BPMEM_TEV_COLOR_ENV_C = 0xD8
# BPMEM_TEV_ALPHA_ENV_C = 0xD9
# BPMEM_TEV_COLOR_ENV_D = 0xDA
# BPMEM_TEV_ALPHA_ENV_D = 0xDB
# BPMEM_TEV_COLOR_ENV_E = 0xDC
# BPMEM_TEV_ALPHA_ENV_E = 0xDD
# BPMEM_TEV_COLOR_ENV_F = 0xDE
# BPMEM_TEV_ALPHA_ENV_F = 0xDF

BPMEM_TEV_REGISTER_L_0 = 0xE0
# BPMEM_TEV_REGISTER_H_0 = 0xE1
# BPMEM_TEV_REGISTER_L_1 = 0xE2
# BPMEM_TEV_REGISTER_H_1 = 0xE3
# BPMEM_TEV_REGISTER_L_2 = 0xE4
# BPMEM_TEV_REGISTER_H_2 = 0xE5
# BPMEM_TEV_REGISTER_L_3 = 0xE6
# BPMEM_TEV_REGISTER_H_3 = 0xE7

# BPMEM_TEV_FOG_RANGE = 0xE8
# BPMEM_TEV_FOG_PARAM_0 = 0xEE
# BPMEM_TEV_FOG_B_MAGNITUDE = 0xEF
# BPMEM_TEV_FOG_B_EXPONENT = 0xF0
# BPMEM_TEV_FOG_PARAM_3 = 0xF1
# BPMEM_TEV_FOG_COLOR = 0xF2

BPMEM_ALPHACOMPARE = 0xF3
# BPMEM_BIAS = 0xF4
# BPMEM_ZTEX2 = 0xF5

BPMEM_TEV_KSEL0 = 0xF6
# BPMEM_TEV_KSEL1 = 0xF7
# BPMEM_TEV_KSEL2 = 0xF8
# BPMEM_TEV_KSEL3 = 0xF9
# BPMEM_TEV_KSEL4 = 0xFA
# BPMEM_TEV_KSEL5 = 0xFB
# BPMEM_TEV_KSEL6 = 0xFC
# BPMEM_TEV_KSEL7 = 0xFD

BPMEM_BP_MASK = 0xFE
