from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackTex0(PackSubfile):
    def pack(self, subfile, binfile):
        super().pack(subfile, binfile)
        binfile.write('I2H3IfI', 0, subfile.width, subfile.height, subfile.format, subfile.num_images, 0, subfile.num_mips, 0)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(subfile.data)
        binfile.end()
