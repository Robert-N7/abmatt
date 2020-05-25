#!/usr/bin/python
''' XF (Transform Unit) Register '''
class XFRegister():
    def __init__(self, enabled, address):
        self.enabled = 0x10 if enabled else 0
        self.address = address
        self.tsize = 0

    def _unpack(self, binfile):
        ''' unpacks header and returns size '''
        self.enabled, self.tsize, self.address = binfile.read("B2H", 5)
        return self.tsize

    def _pack(self, binfile):
        ''' packs header and returns size '''
        binfile.write("B2H", self.enabled, self.tsize, self.address)
        return self.tsize

class XFTexMatrix(XFRegister):
    PROJECTION = ("st", "stq")
    INPUTFORM = ("ab11", "abc1")
    TYPE = ("regular", "embossmap", "color0", "color1")
    COORDINATES = ("geometry", "normals", "colors", "binomialst", "binomialsb")
    def __init__(self, n, enabled = True):
        ''' Nth layer index '''
        super(XFTexMatrix, self).__init__(enabled, 0x1040 | n)
        self.data = {
            "projection"    : 0
            "inputform"     : 0
            "type"          : 0
            "coordinates"   : 5
            "embosssource"  : 5
            "embosslight"   : 0
            "normalize"     : False
        }

    def __getitem__(self, key):
        return self.data[key]

    def unpack(self, binfile):
        ''' unpacks XFTexMatrix '''
        self._unpack(binfile)
        if self.enabled:
            x = binfile.read("I", 4)
            self["projection"] = x >> 1 & 1
            self["inputform"] = x >> 2 & 1
            self["type"] = x >> 4 & 7
            self["coordinates"] = x >> 7 & 0x1f
            self["embosssource"] = x >> 0xc & 7
            self["normalize"] = x >> 0xf & 1
        else:
            binfile.advance(4)

    def pack(self, binfile):
        if self.enabled:
            self._pack(binfile)
            d = self["projection"] << 1 | self["inputform"] << 2 | self["type"] << 4
                | self["coordinates"] << 7 | self["embosssource"] << 0xc
                | self["normalize"] << 0xf
            binfile.write("I", d)
        else:
            binfile.advance(9)

class XFPostEffectMatrix(XFRegister):
    ''' typically follows Tex matrix '''
    def __init__(self, n, enabled = True):
        super(XFPostEffectMatrix, self).__init__(enabled, 0x1050 | n)
        self.data = 0
