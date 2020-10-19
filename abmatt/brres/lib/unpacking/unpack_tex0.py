from brres.lib.unpacking.unpack_subfile import UnpackSubfile


class UnpackTex0(UnpackSubfile):
    def unpack(self, subfile, binfile):
        super().unpack(subfile, binfile)
        _, subfile.width, subfile.height, subfile.format, \
            subfile.num_images, _, subfile.num_mips, _ = binfile.read('I2H3IfI', 0x1c)
        binfile.recall()
        subfile.data = binfile.readRemaining()
        binfile.end()
