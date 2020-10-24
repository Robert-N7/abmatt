
def unpack_tex_matrix(binfile):
    """Unpacks Wii graphics """
    x = unpack_xf_command(binfile)
    # project input type
    # coord source light
    return x >> 1 & 1, x >> 2 & 3, x >> 4 & 7, \
        x >> 7 & 0x1f, x >> 0xc & 7, x >> 0xf & 0xffff


def unpack_dual_tex_matrix(binfile):
    d = unpack_xf_command(binfile)
    # normalize
    return d >> 8 & 1


def unpack_xf_command(binfile):
    enabled, tsize, address = binfile.read("B2H", 5)
    if not enabled:
        binfile.advance(4)
        return 0
    elif tsize <= 0:
        return binfile.read('I', 4)[0]
    else:
        size = tsize + 1
        return binfile.read("{}I".format(size), size * 4)
