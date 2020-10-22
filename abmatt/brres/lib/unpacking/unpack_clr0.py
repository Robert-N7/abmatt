from brres.clr0.clr0_animation import Clr0Animation
from brres.lib.binfile import Folder
from brres.lib.unpacking.interface import Unpacker
from brres.lib.unpacking.unpack_subfile import UnpackSubfile


class UnpackClr0(UnpackSubfile):
    class UnpackSub(Unpacker):
        def unpack_color_list(self, binfile):
            offset = binfile.offset
            binfile.offset += binfile.read('I', 0)[0]
            li = [binfile.read('4B', 4) for i in range(self.node.framecount)]
            binfile.offset = offset + 4
            return li

        def unpack_flags(self, anim, int_val):
            bit = 1
            for i in range(len(anim.flags)):
                if int_val & bit:
                    anim.flags[i] = True
                bit <<= 1
                if int_val & bit:
                    anim.is_constant[i] = True
                bit <<= 1
            return anim.flags, anim.is_constant

        def unpack(self, anim, binfile):
            binfile.start()
            # data = binfile.read('256B', 0)
            # printCollectionHex(data)
            binfile.advance(4)  # ignore name
            [flags] = binfile.read('I', 4)  # flags: series of exists/isconstant
            enabled, is_constant = self.unpack_flags(anim, flags)
            for i in range(len(enabled)):
                if enabled[i]:
                    anim.entry_masks.append(binfile.read('4B', 4))
                    if is_constant[i]:
                        anim.entries.append(binfile.read('4B', 4))
                    else:
                        anim.entries.append(self.unpack_color_list(binfile))
            binfile.end()
            return anim

    def unpack(self, clr0, binfile):
        super().unpack(clr0, binfile)
        _, clr0.framecount, num_entries, clr0.loop = binfile.read('i2Hi', 12)
        binfile.recall()  # section 0
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            anim = Clr0Animation(folder.recallEntryI(), clr0.framecount, clr0.loop)
            self.UnpackSub(anim, binfile)
            clr0.animations.append(anim)
        binfile.end()
