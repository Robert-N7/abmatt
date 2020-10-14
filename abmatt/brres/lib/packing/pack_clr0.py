from brres.lib.binfile import Folder
from brres.lib.packing.interface import Packer
from brres.lib.packing.pack_subfile import PackSubfile


class PackClr0(PackSubfile):
    class PackSub(Packer):
        def pack_flags(self, anim):
            bit = 1
            ret = 0
            for i in range(len(anim.flags)):
                if anim.flags[i]:
                    ret |= bit
                bit <<= 1
                if anim.is_constant[i]:
                    ret |= bit
                bit <<= 1
            return ret

        def pack(self, clr0, binfile):
            binfile.start()
            binfile.storeNameRef(clr0.name)
            binfile.write('I', self.pack_flags(clr0))
            enabled = clr0.flags
            is_constant = clr0.is_constant
            entries = clr0.entries
            masks = clr0.entry_masks
            color_lists = []
            entry_i = 0
            for i in range(len(enabled)):
                if enabled[i]:
                    binfile.write('4B', *masks[entry_i])
                    if is_constant[i]:
                        binfile.write('4B', *entries[entry_i])
                    else:
                        binfile.mark()  # mark and come back
                        color_lists.append(entries[entry_i])
                    entry_i += 1
            for x in color_lists:
                binfile.createRefFromStored()
                for i in range(clr0.framecount):
                    binfile.write('4B', *x[i])
            binfile.end()

    def pack(self, clr0, binfile):
        super().pack(clr0, binfile)
        animations = clr0.animations
        binfile.write('i2Hi', 0, clr0.framecount, len(animations), clr0.loop)
        binfile.createRef()  # section 0
        folder = Folder(binfile)
        for x in animations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        for x in animations:
            folder.createEntryRefI()
            x.pack(binfile)
        binfile.end()
