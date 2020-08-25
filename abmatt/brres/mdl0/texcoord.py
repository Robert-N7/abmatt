from brres.lib.binfile import printCollectionHex
from brres.mdl0.geometry import Geometry


class TexCoord(Geometry):
    COMP_COUNT = (1, 2)

    def unpack(self, binfile):
        super(TexCoord, self).unpack(binfile)
        self.minimum = binfile.read('2f', 8)
        self.maximum = binfile.read('2f', 8)
        self.unpack_data(binfile)

    def pack(self, binfile):
        super(TexCoord, self).pack(binfile)
        binfile.write('2f', *self.minimum)
        binfile.write('2f', *self.maximum)
        self.pack_data(binfile)
