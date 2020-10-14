from brres.lib.unpacking.interface import Unpacker


class UnpackPoint(Unpacker):
    @property
    def FMT(self):
        return 'B', 'b', 'H', 'h', 'f'

    @property
    def COMP_COUNT(self):
        raise NotImplementedError()

    def unpack(self, point, binfile):
        start = binfile.start()
        l = binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        point.index, comp_count, format, point.divisor, point.stride, point.count = binfile.read('3I2BH', 16)
        try:
            point.comp_count = self.COMP_COUNT[comp_count]
        except IndexError:
            point.comp_count = point.DEFAULT_WIDTH
        try:
            point.format = self.FMT[format]
        except IndexError:
            # determine the format using the file length
            t = binfile.offset
            binfile.recall(pop=False)
            bytes_remaining = start + l - binfile.offset
            width = bytes_remaining // (point.count * point.comp_count)
            if width >= 4:
                point.format = 'f'
            elif width >= 2:        # assumes unsigned
                point.format = 'h'
            else:
                point.format = 'b'
        # print(self)

    def unpack_data(self, point, binfile):
        binfile.recall()
        fmt = '{}{}'.format(point.comp_count, point.format)
        stride = point.stride
        data = []
        for i in range(point.count):
            data.append(binfile.read(fmt, stride))
        binfile.alignAndEnd()
        point.data = data


class UnpackVertex(UnpackPoint):
    @property
    def COMP_COUNT(self):
        return 2, 3

    def unpack(self, vertex, binfile):
        super(UnpackVertex, self).unpack(vertex, binfile)
        vertex.minimum = binfile.read('3f', 12)
        vertex.maximum = binfile.read('3f', 12)
        self.unpack_data(vertex, binfile)


class UnpackNormal(UnpackPoint):
    @property
    def COMP_COUNT(self):
        return 3, 9, 32

    def unpack(self, normal, binfile):
        super(UnpackNormal, self).unpack(normal, binfile)
        if normal.comp_count == 32:     # special case (not really sure the differences in types)
            normal.normal_type = 2
            normal.comp_count = 3
        else:
            normal.normal_type = 1 if normal.comp_count == 9 else 0
        self.unpack_data(normal, binfile)


class UnpackUV(UnpackPoint):
    @property
    def COMP_COUNT(self):
        return 1, 2

    def unpack(self, uv, binfile):
        super(UnpackUV, self).unpack(uv, binfile)
        self.minimum = binfile.read('2f', 8)
        self.maximum = binfile.read('2f', 8)
        self.unpack_data(uv, binfile)
