from brres.lib.binfile import printCollectionHex
from brres.mdl0.geometry import Geometry


class TexCoord(Geometry):

    def encode_data(self, point_collection):
        comp_count = super(TexCoord, self).encode_data(point_collection)
        if comp_count > 2:
            raise ValueError('component count {} for tex coordinate {} out of range'.format(comp_count, self.name))
        self.comp_count = comp_count - 1

    def unpack(self, binfile):
        super(TexCoord, self).unpack(binfile)
        self.minimum = binfile.read('3f', 12)
        self.maximum = binfile.read('3f', 12)
        binfile.recall()
        self.data = binfile.readRemaining()
        binfile.end()

    def pack(self, binfile):
        super(TexCoord, self).pack(binfile)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()