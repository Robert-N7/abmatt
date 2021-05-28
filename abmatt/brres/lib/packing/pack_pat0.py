from abmatt.lib.binfile import Folder
from abmatt.lib.pack_interface import Packer
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackPat0Animation(Packer):
    def pack_frames(self, binfile, textures):
        binfile.create_ref_from(self.offset)
        frames = self.node.frames
        binfile.write('2Hf', len(frames), 0, self.node.calcFrameScale())
        for x in frames:
            texture_id = textures.index(x.tex)
            binfile.write('f2H', x.frame_id, texture_id, 0)

    def pack(self, pat0, binfile):
        self.offset = binfile.start()
        binfile.store_name_ref(pat0.name)
        # self.fixedTexture = len(self.frames) <= 1       # todo, check fixed texture formatting/why?
        flags = pat0.enabled | pat0.fixed_texture << 1 | pat0.has_texture << 2 | pat0.has_palette << 3
        binfile.write('I', flags)
        binfile.mark()
        binfile.end()


class PackPat0(PackSubfile):
    def pack(self, pat0, binfile):
        super().pack(pat0, binfile)
        textures = pat0.getTextures()
        anims = pat0.mat_anims
        binfile.write('I4HI', 0, pat0.framecount, len(anims), len(textures), 0, pat0.loop)
        binfile.create_ref()  # section 0: data
        folder = Folder(binfile)  # index group
        for x in anims:
            folder.add_entry(x.name)
        folder.pack(binfile)
        packing = []
        for x in anims:  # Headers/flags
            folder.create_entry_ref_i()
            packing.append(PackPat0Animation(x, binfile))
        for x in packing:  # key frame lists
            x.pack_frames(binfile, textures)

        binfile.create_ref()  # section 1: textures
        binfile.start()
        for x in textures:
            binfile.store_name_ref(x)
        binfile.end()
        binfile.create_ref()  # section 2: palettes
        binfile.create_ref()  # section 3: nulls
        binfile.advance(len(textures) * 4)
        binfile.create_ref()  # section 4: palette ptr table
        binfile.end()
