from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.packing.interface import Packer
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


class PackPat0Animation(Packer):
    def pack_frames(self, binfile, textures):
        binfile.createRefFrom(self.offset)
        frames = self.node.frames
        binfile.write('2Hf', len(frames), 0, self.node.calcFrameScale())
        for x in frames:
            texture_id = textures.index(x.tex)
            binfile.write('f2H', x.frame_id, texture_id, 0)

    def pack(self, pat0, binfile):
        self.offset = binfile.start()
        binfile.storeNameRef(pat0.name)
        # self.fixedTexture = len(self.frames) <= 1       # todo, check fixed texture formatting/why?
        flags = pat0.enabled | pat0.fixedTexture << 1 | pat0.hasTexture << 2 | pat0.hasPalette << 3
        binfile.write('I', flags)
        binfile.mark()
        binfile.end()


class PackPat0(PackSubfile):
    def pack(self, pat0, binfile):
        super().pack(pat0, binfile)
        textures = pat0.getTextures()
        anims = pat0.mat_anims
        binfile.write('I4HI', 0, pat0.framecount, len(anims), len(textures), 0, pat0.loop)
        binfile.createRef()  # section 0: data
        folder = Folder(binfile)  # index group
        for x in anims:
            folder.addEntry(x.name)
        folder.pack(binfile)
        packing = []
        for x in anims:  # Headers/flags
            folder.createEntryRefI()
            packing.append(PackPat0Animation(x, binfile))
        for x in packing:  # key frame lists
            x.pack_frames(binfile, textures)

        binfile.createRef()  # section 1: textures
        binfile.start()
        for x in textures:
            binfile.storeNameRef(x)
        binfile.end()
        binfile.createRef()  # section 2: palettes
        binfile.createRef()  # section 3: nulls
        binfile.advance(len(textures) * 4)
        binfile.createRef()  # section 4: palette ptr table
        binfile.end()
