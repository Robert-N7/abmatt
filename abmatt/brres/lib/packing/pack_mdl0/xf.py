
def pack_vt_specs(binfile, vt_specs):
    pack_xf(binfile, VT_SPECS, vt_specs)


def pack_dual_tex(binfile, index, normalize):
    data = (index * 3) & 0xff | (normalize & 1) << 8
    pack_xf(binfile, XF_DUALTEX0_ID | index, data)


def pack_tex_matrix(binfile, index,
                    project, input, type, coord, emboss_source, emboss_light):
    data = (project & 1) << 1 | (input & 3) << 2 | (type & 7) << 4 | (coord & 0x1f) << 7 \
        | (emboss_source & 7) << 0xc | (emboss_light & 0xffff) << 0xf
    pack_xf(binfile, XF_TEX0_ID | index, data)


def pack_xf(binfile, address, data, size=1):
    if size <= 1:   # single data case
        binfile.write('B2HI', LOAD_XF, 0, address, data)
    else:
        size -= 1
        binfile.write('B2H{}I'.format(size), LOAD_XF, size, address, *data)


# CONSTANTS
LOAD_XF = 0x10

# Size = 0x8000
# Error = 0x1000
# Diag = 0x1001
# State0 = 0x1002
# State1 = 0x1003
# Clock = 0x1004
# ClipDisable = 0x1005
# SetGPMetric = 0x1006
#
VT_SPECS = 0x1008
# SetNumChan = 0x1009
# SetChan0AmbColor = 0x100A
# SetChan1AmbColor = 0x100B
# SetChan0MatColor = 0x100C
# SetChan1MatColor = 0x100D
# SetChan0Color = 0x100E
# SetChan1Color = 0x100F
# SetChan0Alpha = 0x1010
# SetChan1Alpha = 0x1011
# DualTex = 0x1012
# SetMatrixIndA = 0x1018
# SetMatrixIndB = 0x1019
# SetViewport = 0x101A
# SetZScale = 0x101C
# SetZOffset = 0x101F
# SetProjection = 0x1020
# SetNumTexGens = 0x103F
# SetTexMtxInfo = 0x1040
# SetPosMtxInfo = 0x1050
#
# XF_INVTXSPEC_ID = 0x1008
# XF_NUMCOLORS_ID = 0x1009
# XF_NUMTEX_ID = 0x103f
#
XF_TEX0_ID = 0x1040
# XF_TEX1_ID = 0x1041
# XF_TEX2_ID = 0x1042
# XF_TEX3_ID = 0x1043
# XF_TEX4_ID = 0x1044
# XF_TEX5_ID = 0x1045
# XF_TEX6_ID = 0x1046
# XF_TEX7_ID = 0x1047
#
XF_DUALTEX0_ID = 0x1050
# XF_DUALTEX1_ID = 0x1051
# XF_DUALTEX2_ID = 0x1052
# XF_DUALTEX3_ID = 0x1053
# XF_DUALTEX4_ID = 0x1054
# XF_DUALTEX5_ID = 0x1055
# XF_DUALTEX6_ID = 0x1056
# XF_DUALTEX7_ID = 0x1057
