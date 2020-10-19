from brres.lib.unpacking.interface import Unpacker
from brres.mdl0.color import Color


class UnpackColor(Unpacker):
    def __init__(self, name, node, binfile):
        color = Color(name, node, binfile)
        super().__init__(color, binfile)

    def unpack(self, color, binfile):
        binfile.start()
        binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        color.index, color.has_alpha, color.format, color.stride, color.flags, color.count = binfile.read('3I2BH', 16)
        binfile.recall()
        color.data = binfile.readRemaining()
        # print('Color {} count {}'.format(self.name, self.count))
        # printCollectionHex(self.data)
        binfile.end()

