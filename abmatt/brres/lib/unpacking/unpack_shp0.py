from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile
from abmatt.brres.shp0.shp0_animation import Shp0Animation, Shp0KeyFrameList


class UnpackShp0(UnpackSubfile):
    class UnpackSub(Unpacker):
        class UnpackFrames(Unpacker):
            def unpack(self, key_frames, binfile):
                num_entries, key_frames.uk = binfile.read('2H', 4)
                for i in range(num_entries):
                    data = binfile.read('3f', 12)
                    key_frames.frames.append(key_frames.Shp0KeyFrame(data[1], data[2], data[0]))

        def unpack_frame_list(self, node, binfile):
            offset = binfile.offset
            binfile.offset += binfile.read('I', 0)[0]
            self.UnpackFrames(node, binfile)
            binfile.offset = offset + 4

        def unpack(self, anim, binfile):
            binfile.start()
            [anim.flags] = binfile.read('I', 4)
            binfile.advance(4)  # name
            anim.name_id, num_entries, anim.fixed_flags, indices_offset = binfile.read('2H2i', 12)
            anim.indices = binfile.read('{}H'.format(num_entries), num_entries * 2)
            binfile.offset = indices_offset + binfile.beginOffset - 4 * num_entries
            for i in range(num_entries):
                shp = Shp0KeyFrameList(anim.indices[i])
                self.unpack_frame_list(shp, binfile)
                anim.entries.append(shp)
            binfile.end()
            return anim

    def unpack(self, shp0, binfile):
        # print('{} Warning: Shp0 not supported, unable to edit'.format(self.parent.name))
        super().unpack(shp0, binfile)
        orig_path, shp0.framecount, num_anim, shp0.loop = binfile.read('I2HI', 12)
        binfile.recall(1)  # Section 1 string list
        binfile.start()
        for i in range(num_anim):
            shp0.strings.append(binfile.unpack_name())
        binfile.end()
        binfile.recall()  # Section 0 Data
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            anim = Shp0Animation(folder.recallEntryI(), shp0)
            self.UnpackSub(anim, binfile)
            shp0.animations.append(anim)
        binfile.end()
