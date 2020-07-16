#!/usr/bin/python
""" XF (Transform Unit) Register """


class XFCommand(object):
    def __init__(self, enabled, address):
        self.enabled = 0x10 if enabled else 0
        self.address = address
        self.tsize = 0

    def _unpack(self, binfile):
        """ unpacks  and returns data """
        self.enabled, self.tsize, self.address = binfile.read("B2H", 5)
        size = self.tsize + 1
        if not self.enabled:
            binfile.advance(4)
            return 0
        return binfile.read("{}I".format(size), size * 4)

    def _pack(self, binfile, data):
        """ packs header and data """
        binfile.write("B2H", self.enabled, self.tsize, self.address)
        binfile.write("{}I".format(self.tsize + 1), data)


class XFTexMatrix(XFCommand):
    PROJECTION = ("st", "stq")
    INPUTFORM = ("ab11", "abc1")
    TYPE = ("regular", "embossmap", "color0", "color1")
    COORDINATES = ("geometry", "normals", "colors", "binomialst", "binomialsb")

    def __init__(self, n, enabled=True):
        """ Nth layer index """
        super(XFTexMatrix, self).__init__(enabled, 0x1040 | n)
        self.data = {
            "projection": 0,
            "inputform": 0,
            "type": 0,
            "coordinates": 5,
            "embosssource": 5,
            "embosslight": 0
        }

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def unpack(self, binfile):
        """ unpacks XFTexMatrix """
        [x] = self._unpack(binfile)
        if x:
            self["projection"] = x >> 1 & 1
            self["inputform"] = x >> 2 & 3
            self["type"] = x >> 4 & 7
            self["coordinates"] = x >> 7 & 0x1f
            self["embosssource"] = x >> 0xc & 7
            self["embosslight"] = x >> 0xf & 0xffff

    def pack(self, binfile):
        if self.enabled:
            d = self["projection"] << 1 | self["inputform"] << 2 | self["type"] << 4 \
                | self["coordinates"] << 7 | self["embosssource"] << 0xc \
                | self["embosslight"] << 0xf
            self._pack(binfile, d)
        else:
            binfile.advance(9)


class XFDualTex(XFCommand):
    """ typically follows Tex matrix """

    def __init__(self, n, enabled=True):
        super(XFDualTex, self).__init__(enabled, 0x1050 | n)
        self.normalize = 0
        self.dualMatrix = n * 3

    def unpack(self, binfile):
        """ unpacks dual tex """
        [d] = self._unpack(binfile)
        if d:
            self.dualMatrix = d & 0xff
            self.normalize = d >> 8 & 1

    def pack(self, binfile):
        """ packs dual tex """
        if self.enabled:
            d = self.normalize << 8 | self.dualMatrix
            self._pack(binfile, d)
        else:
            binfile.advance(9)
