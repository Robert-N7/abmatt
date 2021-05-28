from abmatt.lib.binfile import Folder
from abmatt.lib.pack_interface import Packer
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackShp0(PackSubfile):
    class PackSub(Packer):
        class PackFrames(Packer):
            def pack(self, k_frames, binfile):
                binfile.create_ref_from_stored()  # create the reference to this offset
                frames = k_frames.frames
                binfile.write('2H', len(frames), k_frames.uk)
                for frame in frames:
                    binfile.write('3f', frame.delta, frame.frame_id, frame.value)

        def pack(self, anim, binfile):
            binfile.start()
            binfile.write('I', anim.flags)
            binfile.store_name_ref(anim.name)
            entries = anim.entries
            binfile.write('2Hi', anim.name_id, len(entries), anim.fixed_flags)
            binfile.mark()  # indices offset
            binfile.write('{}H'.format(len(entries)), *anim.indices)
            binfile.align(4)
            binfile.mark(len(entries))
            binfile.create_ref()  # indices offset
            for x in entries:
                self.PackFrames(x, binfile)
            binfile.end()

    def pack(self, shp0, binfile):
        super().pack(shp0, binfile)
        binfile.write('I2HI', 0, shp0.framecount, len(shp0.strings), shp0.loop)
        binfile.create_ref()     # section 0
        folder = Folder(binfile)
        for x in shp0.animations:
            folder.add_entry(x.name)
        folder.pack(binfile)
        for x in shp0.animations:
            folder.create_entry_ref_i()
            self.PackSub(x, binfile)
        binfile.create_ref()     # section 1
        binfile.start()
        for x in shp0.strings:
            binfile.store_name_ref(x)
        binfile.end()
        binfile.end()
