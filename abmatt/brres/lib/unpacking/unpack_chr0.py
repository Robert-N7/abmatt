from brres.lib.binfile import Folder
from brres.lib.unpacking.interface import Unpacker
from brres.lib.unpacking.unpack_subfile import UnpackSubfile


class UnpackChr0(UnpackSubfile):
    def unpack(self, chr0, binfile):
        super().unpack(chr0, binfile)
        _, chr0.framecount, num_entries, chr0.loop, chr0.scaling_rule = binfile.read('I2H2I', 16)
        binfile.recall()  # section 0
        f = Folder(binfile)
        f.unpack(binfile)
        chr0.data = binfile.readRemaining()
        # printCollectionHex(self.data)
        while len(f):
            name = f.recallEntryI()
            chr0.animations.append(chr0.ModelAnim(name, binfile.offset - binfile.beginOffset))
        binfile.end()
