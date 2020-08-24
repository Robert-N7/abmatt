from brres.lib.binfile import printCollectionHex
from brres.mdl0.geometry import Geometry


class TexCoord(Geometry):
    def unpack(self, binfile):
        super(TexCoord, self).unpack(binfile)
        self.minimum = binfile.read('2f', 8)
        self.maximum = binfile.read('2f', 8)
        binfile.recall()
        self.data = binfile.readRemaining()
        binfile.end()

    def pack(self, binfile):
        super(TexCoord, self).pack(binfile)
        binfile.write('2f', *self.minimum)
        binfile.write('2f', *self.maximum)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()