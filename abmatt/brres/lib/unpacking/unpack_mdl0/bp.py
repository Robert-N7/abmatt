from abmatt.brres.lib.unpacking.interface import Unpacker


def unpack_ras1_iref(binfile):
    data = unpack_bp(binfile)
    ind_maps = []
    ind_coords = []
    for i in range(4):
        ind_maps.append(data & 7)
        data >>= 3
        ind_coords.append(data & 7)
        data >>= 3
    return ind_maps, ind_coords


def unpack_ind_cmd(binfile):
    data = unpack_bp(binfile)
    # stage format bias alpha
    # matrix swrap twrap
    # useprevstage unmodifiedLOD
    return data & 3, data >> 2 & 3, data >> 4 & 7, data >> 7 & 3, \
           data >> 9 & 7, data >> 13 & 7, data >> 16 & 7, \
           data >> 19 & 1, data >> 20 & 1


def unpack_alpha_env(binfile):
    data = unpack_bp(binfile)
    # a b c d
    # dest bias op clamp shift
    # tswap rswap
    return data >> 13 & 0x7, data >> 10 & 0x7, data >> 7 & 0x7, data >> 4 & 0x7, \
           data >> 22 & 0x3, data >> 16 & 3, data >> 18 & 1, data >> 19 & 1, data >> 20 & 3, \
           data >> 2 & 3, data & 3


def unpack_color_env(binfile):
    data = unpack_bp(binfile)
    # a b c d
    # dest bias op clamp shift
    return data >> 12 & 0xf, data >> 8 & 0xf, data >> 4 & 0xf, data & 0xf, \
           data >> 22 & 3, data >> 16 & 3, data >> 18 & 1, data >> 19 & 1, data >> 20 & 3


def unpack_tref_helper(data):
    # map coord enable raster
    return data & 7, data >> 3 & 7, data >> 6 & 1, data >> 7 & 7


def unpack_tref(binfile):
    data = unpack_bp(binfile)
    s1 = unpack_tref_helper(data)
    data >>= 12
    s2 = unpack_tref_helper(data)
    return (s1, s2)


def unpack_kcel(binfile):
    data = unpack_bp(binfile)
    # xrgb = data & 3
    # xga = data >> 2 & 3
    constant0 = data >> 4 & 0x1f
    constant_a0 = data >> 9 & 0x1f
    constant1 = data >> 14 & 0x1f
    constant_a1 = data >> 19 & 0x1f
    return constant0, constant_a0, constant1, constant_a1


def unpack_alpha_function(binfile):
    data = unpack_bp(binfile)
    ref0 = data & 0xff
    ref1 = data >> 8 & 0xff
    comp0 = data >> 16 & 0x7
    comp1 = data >> 19 & 0x7
    logic = data >> 22 & 0x3
    return ref0, ref1, comp0, comp1, logic


def unpack_zmode(binfile):
    data = unpack_bp(binfile)
    depth_test = data & 1
    depth_update = data >> 4 & 1
    depth_function = data >> 1 & 7
    return depth_test, depth_update, depth_function


def unpack_blend_mode(binfile):
    data = unpack_bp(binfile)
    # enabled logic, dither, color, alpha
    # subtract, logic_op, source, dest
    return data & 1, data >> 1 & 1, data >> 2 & 1, data >> 3 & 1, data >> 4 & 1, \
        data >> 11 & 1, data >> 12 & 0xf, data >> 8 & 7, data >> 5 & 7


def unpack_constant_alpha(binfile):
    data = unpack_bp(binfile)
    enabled = data >> 8 & 0x1
    alpha = data & 0xff
    return enabled, alpha


class UnpackIndMtx(Unpacker):
    def __init__(self, node, binfile):
        super().__init__(node, binfile)

    def unpack(self, ind_matrix, binfile):
        """ unpacks ind matrix """
        scale = 0
        for i in range(3):
            ind_matrix.enabled, bpmem, data = unpack_bp(binfile, return_enabled=True)
            if not ind_matrix.enabled:
                binfile.advance(10)  # skip ahead
                ind_matrix.scale = scale
                return
            # parse data
            if i == 0:
                ind_matrix.id = (bpmem - ind_matrix.BPMEM_IND_MTXA0) // 3
            scale = scale | (data >> 22 & 3) << (2 * i)
            ind_matrix.matrix[0][i] = self.force11bitFloat(data & 0x7ff)  # row 0
            ind_matrix.matrix[1][i] = self.force11bitFloat(data >> 11 & 0x7ff)  # row 1
        ind_matrix.scale = scale - 17

    def force11bitFloat(self, val):
        """Forces 11 bit to float
            100 0000 0000 sign
            011 1111 1111 mantissa
        """
        # There's probably a better way to do this
        f = 0.0
        bitn = 10
        start = 1 << bitn
        while bitn > 0:
            # print("divisor {} bitn {}".format(start, bitn))
            if val & 1:
                f += 1.0 / start
                # print(f)
            val >>= 1
            start >>= 1
            bitn -= 1
        if val & 1:  # sign
            f *= -1
        return f


def unpack_color(binfile, is_constant):
    red, alpha = unpack_color_reg(binfile)
    green, blue = unpack_color_reg(binfile)
    if not is_constant:
        binfile.advance(10)
    return red, green, blue, alpha


def unpack_color_reg(binfile):
    data = unpack_bp(binfile)
    return data >> 12 & 0x7ff, data & 0xfff


def unpack_bp(binfile, return_enabled=False):
    bp, data = binfile.read('BI', 5)
    assert bp == 0 or bp == 0x61
    bp_mem = data >> 24
    data = data & 0xffffff
    if return_enabled:
        return bp, bp_mem, data
    return data
