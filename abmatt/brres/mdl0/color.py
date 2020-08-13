from struct import pack

from brres.lib.node import Node


class Color(Node):

    def begin(self):
        self.flags = 0
        self.index = 0
        # the rest done by encode_data

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

    def __len__(self):
        return self.count

    def encode_data(self, color_collection):
        form = color_collection.encode_format
        rgba_colors = color_collection.rgba_colors
        self.format = form
        if form < 3:
            self.stride = form + 2
            self.has_alpha = False
        else:
            self.has_alpha = True
            self.stride = form - 1
        self.count = len(rgba_colors)
        if form == 0:
            self.data = self.encode_rgb565(rgba_colors)
        elif form == 1:
            self.data = self.encode_rgb8(rgba_colors)
        elif form == 2 or form == 5:
            self.data = self.encode_rgba8(rgba_colors)
        elif form == 3:
            self.data = self.encode_rgba4(rgba_colors)
        elif form == 4:
            self.data = self.encode_rgba6(rgba_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(self.name, form))

    def unpack(self, binfile):
        binfile.start()
        binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, self.has_alpha, self.format, self.stride, self.flags, self.count = binfile.read('3I2BH', 16)
        binfile.recall()
        self.data = binfile.readRemaining()
        binfile.end()

    def pack(self, binfile):
        binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.mark()
        binfile.storeNameRef(self.name)
        binfile.write('3I2BH', self.index, self.has_alpha, self.format, self.stride, self.flags, self.count)
        binfile.align()
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()


class ColorCollection:
    def __init__(self, rgba_colors, face_indices, encode_format=5):
        """
        :param rgba_colors: [[r,g,b,a], ...]
        :param face_indices: ndarray, list of indexes for each triangle [[tri_index0, tri_index1, tri_index2], ...]
        :param encode_format: (0=rgb565|1=rgb8|2=rgb32|3=rgba4|4=rgba6|5=rgba8)
        """
        self.rgba_colors = rgba_colors
        self.face_indices = face_indices
        self.encode_format = encode_format
