from struct import unpack_from, unpack

import numpy as np

from abmatt.autofix import AutoFix


def decode_geometry_group(geometry):
    arr = np.array(geometry.data, np.float)
    if geometry.divisor:
        arr = arr / (2 ** geometry.divisor)
    return arr


class ColorDecoder:
    @staticmethod
    def decode_data(color):
        form = color.format
        num_colors = len(color)
        data = color.data
        if form == 0:
            data = ColorDecoder.decode_rgb565(data, num_colors)
        elif form == 1:
            data = ColorDecoder.decode_rgb8(data, num_colors)
        elif form == 2 or form == 5:
            data = ColorDecoder.decode_rgba8(data, num_colors)
            if form == 2:
                data[:, 3] = 0xff
        elif form == 3:
            data = ColorDecoder.decode_rgba4(data, num_colors)
        elif form == 4:
            data = ColorDecoder.decode_rgba6(data, num_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return np.array(data, np.uint8)

    @staticmethod
    def decode_rgb565(color_data, num_colors):
        data = unpack('>{}H'.format(num_colors), color_data)
        colors = []
        for color in data:
            colors.append(((color >> 8) & 0xf8, (color >> 3) & 0xfc, (color & 0x1f) << 3, 0xff))
        return colors

    @staticmethod
    def decode_rgb8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            c = list(unpack_from('>3B', data, offset))
            c.append(0xff)
            colors.append(c)
            offset += 3
        return colors

    @staticmethod
    def decode_rgba8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            colors.append(unpack_from('>4B', data, offset))
            offset += 4
        return colors

    @staticmethod
    def decode_rgba4(data, num_colors):
        colors = []
        c_data = unpack('>{}H'.format(num_colors), data)
        for color in c_data:
            colors.append((color >> 8 & 0xf0, color >> 4 & 0xf0,
                           color & 0xf0, color << 4 & 0xf0))
        return colors

    @staticmethod
    def decode_rgba6(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            d = unpack_from('>3B', data, offset)
            colors.append((d[0] & 0xfc, (d[0] & 0x3) << 6 | (d[1] & 0xf0) >> 2,
                           d[1] << 4 & 0xf0 | d[2] >> 4 & 0xc, d[2] << 2 & 0xfc))
            offset += 3
        return colors
