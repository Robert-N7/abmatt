from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackChr0(PackSubfile):
    def pack(self, chr0, binfile):
        super().pack(chr0, binfile)
        binfile.write('I2H2I', 0, chr0.framecount, len(chr0.animations), chr0.loop, chr0.scaling_rule)
        f = Folder(binfile)
        for x in chr0.animations:
            f.addEntry(x.name)
        binfile.createRef()
        f.pack(binfile)
        binfile.writeRemaining(chr0.data)
        for x in chr0.animations:  # hackish way of overwriting the string offsets
            binfile.offset = binfile.beginOffset + x.offset
            f.createEntryRefI()
            binfile.storeNameRef(x.name)
        binfile.end()