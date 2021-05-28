from abmatt.lib.binfile import Folder
from abmatt.lib.pack_interface import Packer
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackChr0(PackSubfile):
    def pack(self, chr0, binfile):
        super().pack(chr0, binfile)
        binfile.write('I2H2I', 0, chr0.framecount, len(chr0.animations), chr0.loop, chr0.scaling_rule)
        f = Folder(binfile)
        for x in chr0.animations:
            f.add_entry(x.name)
        binfile.create_ref()
        f.pack(binfile)
        binfile.write_remaining(chr0.data)
        for x in chr0.animations:  # hackish way of overwriting the string offsets
            binfile.offset = binfile.beginOffset + x.offset
            f.create_entry_ref_i()
            PackChr0BoneAnimation(x, binfile)
        binfile.end()


class PackChr0BoneAnimation(Packer):
    def pack(self, node, binfile):
        binfile.start()
        binfile.store_name_ref(node.name)
        binfile.end()