''' Dealing with Wii graphics, much of which courtesy of Brawlbox
    https://github.com/libertyernie/brawltools
'''


class BPCommand(object):
    def __init__(self, bpmem, data=0, enabled = True):
        self.bpmem = bpmem
        self.data = data
        self.enabled = 0x61 & enabled

    def pack(self, binfile):
        binfile.write("3BH", self.enabled, self.bpmem, self.data >> 16, self.data)

    def unpack(self, binfile):
        bt = binfile.read("3BH", 5)
        self.enabled = bt[0]
        self.bpmem = bt[1]
        self.data = bt[2] << 16 | bt[3]

    # bpmem Constants
    BPMEM_GENMODE = 0x00,

    BPMEM_DISPLAYCOPYFILER0 = 0x01,
    BPMEM_DISPLAYCOPYFILER1 = 0x02,
    BPMEM_DISPLAYCOPYFILER2 = 0x03,
    BPMEM_DISPLAYCOPYFILER3 = 0x04,
    BPMEM_DISPLAYCOPYFILER4 = 0x05,

    BPMEM_IND_MTXA0 = 0x06,
    BPMEM_IND_MTXB0 = 0x07,
    BPMEM_IND_MTXC0 = 0x08,
    BPMEM_IND_MTXA1 = 0x09,
    BPMEM_IND_MTXB1 = 0x0A,
    BPMEM_IND_MTXC1 = 0x0B,
    BPMEM_IND_MTXA2 = 0x0C,
    BPMEM_IND_MTXB2 = 0x0D,
    BPMEM_IND_MTXC2 = 0x0E,
    BPMEM_IND_IMASK = 0x0F,

    BPMEM_IND_CMD0 = 0x10,
    BPMEM_IND_CMD1 = 0x11,
    BPMEM_IND_CMD2 = 0x12,
    BPMEM_IND_CMD3 = 0x13,
    BPMEM_IND_CMD4 = 0x14,
    BPMEM_IND_CMD5 = 0x15,
    BPMEM_IND_CMD6 = 0x16,
    BPMEM_IND_CMD7 = 0x17,
    BPMEM_IND_CMD8 = 0x18,
    BPMEM_IND_CMD9 = 0x19,
    BPMEM_IND_CMDA = 0x1A,
    BPMEM_IND_CMDB = 0x1B,
    BPMEM_IND_CMDC = 0x1C,
    BPMEM_IND_CMDD = 0x1D,
    BPMEM_IND_CMDE = 0x1E,
    BPMEM_IND_CMDF = 0x1F,

    BPMEM_SCISSORTL = 0x20,
    BPMEM_SCISSORBR = 0x21,
    BPMEM_LINEPTWIDTH = 0x22,
    BPMEM_PERF0_TRI = 0x23,
    BPMEM_PERF0_QUAD = 0x24,

    BPMEM_RAS1_SS0 = 0x25,
    BPMEM_RAS1_SS1 = 0x26,
    BPMEM_IREF = 0x27,

    BPMEM_TREF0 = 0x28,
    BPMEM_TREF1 = 0x29,
    BPMEM_TREF2 = 0x2A,
    BPMEM_TREF3 = 0x2B,
    BPMEM_TREF4 = 0x2C,
    BPMEM_TREF5 = 0x2D,
    BPMEM_TREF6 = 0x2E,
    BPMEM_TREF7 = 0x2F,

    BPMEM_SU_SSIZE0 = 0x30,
    BPMEM_SU_TSIZE0 = 0x31,
    BPMEM_SU_SSIZE1 = 0x32,
    BPMEM_SU_TSIZE1 = 0x33,
    BPMEM_SU_SSIZE2 = 0x34,
    BPMEM_SU_TSIZE2 = 0x35,
    BPMEM_SU_SSIZE3 = 0x36,
    BPMEM_SU_TSIZE3 = 0x37,
    BPMEM_SU_SSIZE4 = 0x38,
    BPMEM_SU_TSIZE4 = 0x39,
    BPMEM_SU_SSIZE5 = 0x3A,
    BPMEM_SU_TSIZE5 = 0x3B,
    BPMEM_SU_SSIZE6 = 0x3C,
    BPMEM_SU_TSIZE6 = 0x3D,
    BPMEM_SU_SSIZE7 = 0x3E,
    BPMEM_SU_TSIZE7 = 0x3F,

    BPMEM_ZMODE = 0x40,
    BPMEM_BLENDMODE = 0x41,
    BPMEM_CONSTANTALPHA = 0x42,
    BPMEM_ZCOMPARE = 0x43,
    BPMEM_FIELDMASK = 0x44,
    BPMEM_SETDRAWDONE = 0x45,
    BPMEM_BUSCLOCK0 = 0x46,
    BPMEM_PE_TOKEN_ID = 0x47,
    BPMEM_PE_TOKEN_INT_ID = 0x48,

    BPMEM_EFB_TL = 0x49,
    BPMEM_EFB_BR = 0x4A,
    BPMEM_EFB_ADDR = 0x4B,

    BPMEM_MIPMAP_STRIDE = 0x4D,
    BPMEM_COPYYSCALE = 0x4E,

    BPMEM_CLEAR_AR = 0x4F,
    BPMEM_CLEAR_GB = 0x50,
    BPMEM_CLEAR_Z = 0x51,

    BPMEM_TRIGGER_EFB_COPY = 0x52,
    BPMEM_COPYFILTER0 = 0x53,
    BPMEM_COPYFILTER1 = 0x54,
    BPMEM_CLEARBBOX1 = 0x55,
    BPMEM_CLEARBBOX2 = 0x56,

    BPMEM_UNKNOWN_57 = 0x57,

    BPMEM_REVBITS = 0x58,
    BPMEM_SCISSOROFFSET = 0x59,

    BPMEM_UNKNOWN_60 = 0x60,
    BPMEM_UNKNOWN_61 = 0x61,
    BPMEM_UNKNOWN_62 = 0x62,

    BPMEM_TEXMODESYNC = 0x63,
    BPMEM_LOADTLUT0 = 0x64,
    BPMEM_LOADTLUT1 = 0x65,
    BPMEM_TEXINVALIDATE = 0x66,
    BPMEM_PERF1 = 0x67,
    BPMEM_FIELDMODE = 0x68,
    BPMEM_BUSCLOCK1 = 0x69,

    BPMEM_TX_SETMODE0_A = 0x80,
    BPMEM_TX_SETMODE0_B = 0x81,
    BPMEM_TX_SETMODE0_C = 0x82,
    BPMEM_TX_SETMODE0_D = 0x83,

    BPMEM_TX_SETMODE1_A = 0x84,
    BPMEM_TX_SETMODE1_B = 0x85,
    BPMEM_TX_SETMODE1_C = 0x86,
    BPMEM_TX_SETMODE1_D = 0x87,

    BPMEM_TX_SETIMAGE0_A = 0x88,
    BPMEM_TX_SETIMAGE0_B = 0x89,
    BPMEM_TX_SETIMAGE0_C = 0x8A,
    BPMEM_TX_SETIMAGE0_D = 0x8B,

    BPMEM_TX_SETIMAGE1_A = 0x8C,
    BPMEM_TX_SETIMAGE1_B = 0x8D,
    BPMEM_TX_SETIMAGE1_C = 0x8E,
    BPMEM_TX_SETIMAGE1_D = 0x8F,

    BPMEM_TX_SETIMAGE2_A = 0x90,
    BPMEM_TX_SETIMAGE2_B = 0x91,
    BPMEM_TX_SETIMAGE2_C = 0x92,
    BPMEM_TX_SETIMAGE2_D = 0x93,

    BPMEM_TX_SETIMAGE3_A = 0x94,
    BPMEM_TX_SETIMAGE3_B = 0x95,
    BPMEM_TX_SETIMAGE3_C = 0x96,
    BPMEM_TX_SETIMAGE3_D = 0x97,

    BPMEM_TX_SETTLUT_A = 0x98,
    BPMEM_TX_SETTLUT_B = 0x99,
    BPMEM_TX_SETTLUT_C = 0x9A,
    BPMEM_TX_SETTLUT_D = 0x9B,

    BPMEM_TX_SETMODE0_4_A = 0xA0,
    BPMEM_TX_SETMODE0_4_B = 0xA1,
    BPMEM_TX_SETMODE0_4_C = 0xA2,
    BPMEM_TX_SETMODE0_4_D = 0xA3,

    BPMEM_TX_SETMODE1_4_A = 0xA4,
    BPMEM_TX_SETMODE1_4_B = 0xA5,
    BPMEM_TX_SETMODE1_4_C = 0xA6,
    BPMEM_TX_SETMODE1_4_D = 0xA7,

    BPMEM_TX_SETIMAGE0_4_A = 0xA8,
    BPMEM_TX_SETIMAGE0_4_B = 0xA9,
    BPMEM_TX_SETIMAGE0_4_C = 0xAA,
    BPMEM_TX_SETIMAGE0_4_D = 0xAB,

    BPMEM_TX_SETIMAGE1_4_A = 0xAC,
    BPMEM_TX_SETIMAGE1_4_B = 0xAD,
    BPMEM_TX_SETIMAGE1_4_C = 0xAE,
    BPMEM_TX_SETIMAGE1_4_D = 0xAF,

    BPMEM_TX_SETIMAGE2_4_A = 0xB0,
    BPMEM_TX_SETIMAGE2_4_B = 0xB1,
    BPMEM_TX_SETIMAGE2_4_C = 0xB2,
    BPMEM_TX_SETIMAGE2_4_D = 0xB3,

    BPMEM_TX_SETIMAGE3_4_A = 0xB4,
    BPMEM_TX_SETIMAGE3_4_B = 0xB5,
    BPMEM_TX_SETIMAGE3_4_C = 0xB6,
    BPMEM_TX_SETIMAGE3_4_D = 0xB7,

    BPMEM_TX_SETLUT_4_A = 0xB8,
    BPMEM_TX_SETLUT_4_B = 0xB9,
    BPMEM_TX_SETLUT_4_C = 0xBA,
    BPMEM_TX_SETLUT_4_D = 0xBB,

    BPMEM_UNKNOWN_BC = 0xBC,
    BPMEM_UNKNOWN_BB = 0xBB,
    BPMEM_UNKNOWN_BD = 0xBD,
    BPMEM_UNKNOWN_BE = 0xBE,
    BPMEM_UNKNOWN_BF = 0xBF,

    BPMEM_TEV_COLOR_ENV_0 = 0xC0,
    BPMEM_TEV_ALPHA_ENV_0 = 0xC1,
    BPMEM_TEV_COLOR_ENV_1 = 0xC2,
    BPMEM_TEV_ALPHA_ENV_1 = 0xC3,
    BPMEM_TEV_COLOR_ENV_2 = 0xC4,
    BPMEM_TEV_ALPHA_ENV_2 = 0xC5,
    BPMEM_TEV_COLOR_ENV_3 = 0xC6,
    BPMEM_TEV_ALPHA_ENV_3 = 0xC7,
    BPMEM_TEV_COLOR_ENV_4 = 0xC8,
    BPMEM_TEV_ALPHA_ENV_4 = 0xC9,
    BPMEM_TEV_COLOR_ENV_5 = 0xCA,
    BPMEM_TEV_ALPHA_ENV_5 = 0xCB,
    BPMEM_TEV_COLOR_ENV_6 = 0xCC,
    BPMEM_TEV_ALPHA_ENV_6 = 0xCD,
    BPMEM_TEV_COLOR_ENV_7 = 0xCE,
    BPMEM_TEV_ALPHA_ENV_7 = 0xCF,
    BPMEM_TEV_COLOR_ENV_8 = 0xD0,
    BPMEM_TEV_ALPHA_ENV_8 = 0xD1,
    BPMEM_TEV_COLOR_ENV_9 = 0xD2,
    BPMEM_TEV_ALPHA_ENV_9 = 0xD3,
    BPMEM_TEV_COLOR_ENV_A = 0xD4,
    BPMEM_TEV_ALPHA_ENV_A = 0xD5,
    BPMEM_TEV_COLOR_ENV_B = 0xD6,
    BPMEM_TEV_ALPHA_ENV_B = 0xD7,
    BPMEM_TEV_COLOR_ENV_C = 0xD8,
    BPMEM_TEV_ALPHA_ENV_C = 0xD9,
    BPMEM_TEV_COLOR_ENV_D = 0xDA,
    BPMEM_TEV_ALPHA_ENV_D = 0xDB,
    BPMEM_TEV_COLOR_ENV_E = 0xDC,
    BPMEM_TEV_ALPHA_ENV_E = 0xDD,
    BPMEM_TEV_COLOR_ENV_F = 0xDE,
    BPMEM_TEV_ALPHA_ENV_F = 0xDF,

    BPMEM_TEV_REGISTER_L_0 = 0xE0,
    BPMEM_TEV_REGISTER_H_0 = 0xE1,
    BPMEM_TEV_REGISTER_L_1 = 0xE2,
    BPMEM_TEV_REGISTER_H_1 = 0xE3,
    BPMEM_TEV_REGISTER_L_2 = 0xE4,
    BPMEM_TEV_REGISTER_H_2 = 0xE5,
    BPMEM_TEV_REGISTER_L_3 = 0xE6,
    BPMEM_TEV_REGISTER_H_3 = 0xE7,

    BPMEM_TEV_FOG_RANGE = 0xE8,
    BPMEM_TEV_FOG_PARAM_0 = 0xEE,
    BPMEM_TEV_FOG_B_MAGNITUDE = 0xEF,
    BPMEM_TEV_FOG_B_EXPONENT = 0xF0,
    BPMEM_TEV_FOG_PARAM_3 = 0xF1,
    BPMEM_TEV_FOG_COLOR = 0xF2,

    BPMEM_ALPHACOMPARE = 0xF3,
    BPMEM_BIAS = 0xF4,
    BPMEM_ZTEX2 = 0xF5,

    BPMEM_TEV_KSEL0 = 0xF6,
    BPMEM_TEV_KSEL1 = 0xF7,
    BPMEM_TEV_KSEL2 = 0xF8,
    BPMEM_TEV_KSEL3 = 0xF9,
    BPMEM_TEV_KSEL4 = 0xFA,
    BPMEM_TEV_KSEL5 = 0xFB,
    BPMEM_TEV_KSEL6 = 0xFC,
    BPMEM_TEV_KSEL7 = 0xFD,

    BPMEM_BP_MASK = 0xFE


class ZMode(BPCommand):
    ''' Depth settings '''
    def __init__(self, enableDepthTest = True, enableDepthUpdate = True):
        super(ZMode, self).__init__(BPCommand.BPMEM_ZMODE,
            enableDepthUpdate << 4 | 0xe | enableDepthTest)

    def getDepthTest(self):
        return self.data & 1
    def setDepthTest(self, enable):
        self.data = (enable | 0xfe) & self.data

    def getDepthUpdate(self):
        return self.data >> 4 & 1
    def setDepthUpdate(self, enable):
        self.data = self.data & (enable << 4 | 0xf)

    def getDepthFunction(self):
        return self.data >> 1 & 7
    def setDepthFunction(self, ival):
        ''' never 0, < 1, = 2, <= 3, > 4, != 5, >= 6, always 7 '''
        self.data = self.data & (ival << 1 | 0xf1)

class AlphaFunction(BPCommand):
    ''' Alpha function '''
    def __init__(self, xlu = False):
        data = 0x1eff80 if xlu else 0x3f0000
        super(AlphaFunction, self).__init__(BPCommand.BPMEM_ALPHACOMPARE, data)

    def isXlu(self):
        return not (self.data >> 16 & 0x3f)  # just checks comparison functions

    def setXlu(self, enable):
        if enable:
            if not self.getRef0():
                self.setRef0(0x80)
            if not self.getRef1():
                self.setRef1(0xff)
            self.setComp0(6)
            self.setComp1(3)
        else:
            self.setComp0(7)
            self.setComp1(7)

    def getRef0(self):
        return self.data & 0xff
    def setRef0(self, val):
        self.data = self.data & 0xffff00 | val

    def getRef1(self):
        return self.data >> 8 & 0xff
    def setRef1(self, val):
        self.data = self.data & 0xff00ff | val << 8

    def getComp0(self):
        return self.data >> 16 & 0x7
    def setComp0(self, val):
        ''' never 0, < 1, = 2, <= 3, > 4, != 5, >= 6, always 7 '''
        self.data = self.data & 0xf8ffff | val << 16

    def getComp1(self):
        return self.data >> 19 & 0x7
    def setComp1(self, val):
        self.data = self.data & 0xc7ffff | val << 19

    def getLogic(self):
        return self.data >> 22 & 0x3
    def setLogic(self, val):
        ''' and 0, or 1, exclusiveor 2, inverseExclusiveOr 3 '''
        self.data = self.data & 0x3fffff | val << 22

class BlendMode(BPCommand):
    ''' Blend Mode '''
    def __init__(self, enabled = False):
        super(BlendMode, self).__init__(BPCommand.BPMEM_BLENDMODE, 0x34A0 | enabled)

    def isEnabled(self):
        return self.data & 1
    def setEnabled(self, enable):
        self.data = self.data & 0xfffffe | enable

    def getBlendLogic(self):
        return self.data >> 12 & 0xf
    def setBlendLogic(self, ival):
        self.data = self.data & 0x0fff | ival << 12
    def getSrcFactor(self):
        return self.data >> 8 & 7
    def setSrcFactor(self, ival):
        self.data = self.data & 0xf8ff | ival << 8
    def getDstFactor(self):
        return self.data >> 5 & 7
    def setDstFactor(self, ival):
        self.data = self.data & 0xff1f | ival << 5


class ConstantAlpha(BPCommand):
    ''' constant alpha '''
    def __init(self, enabled = False):
        data = 0 if not enabled else 0x1ff
        super(ConstantAlpha, self).__init__(BPCommand.BPMEM_CONSTANTALPHA, data)

    def isEnabled(self):
        return self.data >> 8 & 1
    def setEnabled(self, enable):
        self.data = self.data & 0xff | enable << 8
    def get(self):
        return self.data & 0xff
    def set(self, v):
        self.data = self.data & 0x100 | v


class ColorEnv(BPCommand):
    ''' Dealing with color shader ops '''
    def __init__(self):
        super(ColorEnv, self).__init__(0x00)    # todo

    def getSelA(self):
        return self.data >> 12 & 0xf
    def setSelA(self, ival):
        self.data = self.data & 0xff0fff | ival << 12
    def getSelB(self):
        return self.data >> 8 & 0xf
    def setSelB(self, ival):
        self.data = self.data & 0xfff0ff | ival << 8
    def getSelC(self):
        return self.data >> 4 & 0xf
    def setSelC(self, ival):
        self.data = self.data & 0xffff0f | ival << 4
    def getSelD(self):
        return self.data & 0xf
    def setSelD(sef, ival):
        self.data = self.data & 0xfffff0 | ival
    def getDest(self):
        return self.data >> 22 & 0x3
    def setDest(self, ival):
        self.data = self.data & 0x3fffff | ival << 22

class AlphaEnv(BPCommand):
    ''' Dealing with alpha shader ops '''
    def __init__(self):
        super(AlphaEnv, self).__init__(0x00)    # todo

    def getSelA(self):
        return self.data >> 13 & 0x7
    def setSelA(self, ival):
        self.data = self.data & 0xff1fff | ival << 13
    def getSelB(self):
        return self.data >> 10 & 0x7
    def setSelB(self, ival):
        self.data = self.data & 0xffe3ff | ival << 10
    def getSelC(self):
        return self.data >> 7 & 0x7
    def setSelC(self, ival):
        self.data = self.data & 0xfffc7f | ival << 7
    def getSelD(self):
        return self.data >> 4 & 0x7
    def setSelD(sef, ival):
        self.data = self.data & 0xffff8f | ival << 4
    def getDest(self):
        return self.data >> 22 & 0x3
    def setDest(self, ival):
        self.data = self.data & 0x3fffff | ival << 22

class RAS1_IRef(BPCommand):
    def __init__(self):
        pass # todo

class ColorReg(BPCommand):
    ''' Tev registers '''
    def __init__(self, register, high, type, data = 0):
        ''' Color register
            register: 0-4
            high: 0- low, 1 - high
            type: 0-1
            data: color data
                //0000 0000 0000 1111 1111 1111 Red (Lo) / Blue (Hi)
                //0111 1111 1111 0000 0000 0000 Alpha (Lo) /Green (Hi)
        '''
        super(ColorReg, self).__init__(0xE0 + (2 * register) + high, data)
    def getColor(self):
        ''' returns (alpha, red) if low, (green, blue) if high. '''
        return [self.data >> 12 & 0x7ff, self.data & 0xfff]
    def setColor(self, color):
        ''' color: (alpha, red) | (green, blue) '''
        self.data = self.data & 0x800000 | color[0] << 12 | color[1]
