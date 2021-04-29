from struct import pack

import numpy as np

from abmatt.converters.points import consolidate_data


class ColorCollection:

    def __init__(self, rgba_colors, face_indices, encode_format=None, normalize=False):
        """
        :param rgba_colors: [[r,g,b,a], ...] between 0-1 denormalized, normalizes to 0-255
        :param face_indices: ndarray, list of indexes for each triangle [[tri_index0, tri_index1, tri_index2], ...]
        :param encode_format: (0=rgb565|1=rgb8|2=rgb32|3=rgba4|4=rgba6|5=rgba8)
        """
        self.rgba_colors = rgba_colors
        if normalize:
            self.normalize()
        self.face_indices = face_indices
        self.encode_format = encode_format
        self.combined_into = None
        self.encoded = None
        self.combined_index = slice(0, len(self.face_indices))

    def __eq__(self, other):
        return other is not None and type(other) == ColorCollection and \
               np.allclose(self.rgba_colors, other.rgba_colors) \
               and self.face_indices == other.face_indices and self.encode_format == other.encode_format

    def get_face_indices(self):
        if self.combined_into:
            return self.combined_into.face_indices[self.combined_index]
        else:
            return self.face_indices[self.combined_index]

    def __len__(self):
        return len(self.rgba_colors)

    def get_encode_format(self):
        """Default encode format, RGB8 or RGBA8"""
        if (self.rgba_colors[:, 3] == 255).all():
            return 1
        return 5

    def get_encoded_color(self):
        if self.combined_into:
            return self.combined_into.get_encoded_color()
        return self.encoded

    def encode_data(self, color, encoder=None):
        if self.combined_into:
            raise RuntimeError('This color is combined and should not be encoded!')
        self.encoded = color
        if encoder is not None:
            encoder.before_encode(self)
        if encoder is None or encoder.should_consolidate():
            rgba_colors = self.rgba_colors = self.consolidate()
        else:
            rgba_colors = self.rgba_colors
        if encoder is not None:
            form = self.encode_format = encoder.get_format()
        else:
            form = self.encode_format if self.encode_format is not None else self.get_encode_format()
        color.format = form
        if form < 3:
            color.stride = form + 2
            color.has_alpha = False
        else:
            color.has_alpha = True
            color.stride = form - 1
        color.count = len(rgba_colors)
        if form == 0:
            color.data = self.encode_rgb565(rgba_colors)
        elif form == 1:
            color.data = self.encode_rgb8(rgba_colors)
        elif form == 2 or form == 5:
            color.data = self.encode_rgba8(rgba_colors)
        elif form == 3:
            color.data = self.encode_rgba4(rgba_colors)
        elif form == 4:
            color.data = self.encode_rgba6(rgba_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        if encoder:
            encoder.after_encode(color)
        return form

    @staticmethod
    def encode_rgb565(colors):
        data = [(x[0] & 0xf8) << 8 | (x[1] & 0xfc) << 3 | x[2] >> 3 for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def encode_rgb8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>3B', x[0], x[1], x[2]))
        return data

    @staticmethod
    def encode_rgba8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>4B', *x))
        return data

    @staticmethod
    def encode_rgba4(colors):
        data = [(x[0] & 0xf0 | x[1] & 0xf) << 8 | x[2] & 0xf0 | x[3] & 0xf for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def encode_rgba6(colors):
        data = bytearray()
        tmp = [(x[0] & 0xfc) << 16 | (x[1] & 0xfc) << 10 | (x[2] & 0xfc) << 4 | x[3] >> 2 for x in colors]
        for x in tmp:
            data.extend(pack('>3B', x >> 16, x >> 8 & 0xff, x & 0xff))
        return data

    def consolidate(self):
        self.rgba_colors, self.face_indices, remapper = consolidate_data(self.rgba_colors, self.face_indices)
        return self.rgba_colors

    def normalize(self):
        """Normalizes data between 0-1 to 0-255"""
        self.rgba_colors = np.around(self.rgba_colors * 255).astype(np.uint8)

    def denormalize(self):
        """Opposite of normalize. returns ndarray converted from 0-255 to 0-1"""
        return self.rgba_colors.astype(np.float) / 255

    def combine(self, color, combine_geometry=False):
        if color.combined_into:
            raise RuntimeError('Color is already combined!')
        if self.combined_into:
            if self.combined_into == color:
                raise RuntimeError('Circular combining of colors!')
            self.combined_into.combine(color, combine_geometry)
        else:
            if combine_geometry:    # Make this apart of the tris
                if self.combined_index.stop != len(self.face_indices):
                    raise RuntimeError('Cannot combine color geometry in previously combined color!')
            if (self.rgba_colors != color.rgba_colors).all():
                color.face_indices += len(self)
                self.rgba_colors = np.append(self.rgba_colors, color.rgba_colors, 0)
            color.combined_index = slice(len(self.face_indices), len(self.face_indices) + len(color.face_indices))
            color.combined_into = self
            self.face_indices = np.append(self.face_indices, color.face_indices, 0)

            if combine_geometry:
                self.combined_index = slice(self.combined_index.start, len(self.face_indices))
