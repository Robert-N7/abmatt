from brres.lib.unpacking.interface import Unpacker


class UnpackColor(Unpacker):
    def unpack(self, color, binfile):
        binfile.start()
        binfile.readLen()
        binfile.advance(4)
        binfile.store()
        binfile.advance(4)
        self.index, color.has_alpha, color.format, color.stride, color.flags, color.count = binfile.read('3I2BH', 16)
        binfile.recall()
        color.data = binfile.readRemaining()
        # print('Color {} count {}'.format(self.name, self.count))
        # printCollectionHex(self.data)
        binfile.end()

