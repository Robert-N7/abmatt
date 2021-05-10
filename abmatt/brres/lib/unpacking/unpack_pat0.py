from abmatt.autofix import AutoFix
from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile
from abmatt.brres.pat0.pat0_material import Pat0MatAnimation


class UnpackPat0Animation(Unpacker):
    def hook_textures(self, textures):
        m = len(textures)
        for x in self.node.frames:
            if x.tex >= m:
                x.tex = textures[0]
                AutoFix.warn('Unpacked Pat0 {} tex_id out of range'.format(self.node.name), 1)
            else:
                x.tex = textures[x.tex]

    def unpack_frames(self, pat0, binfile):
        # frame header
        size, _, scale_factor = binfile.read('2Hf', 8)
        frames = pat0.frames
        for i in range(size):
            frame_id, tex_id, plt_id = binfile.read('f2H', 8)
            if frame_id > pat0.framecount:
                AutoFix.warn('Unpacked Pat0 {} frame index out of range'.format(pat0.name), 1)
                break
            frames.append(pat0.Frame(frame_id, tex_id, plt_id))

    def unpack_flags(self, pat0, binfile):
        binfile.advance(4)  # already have name
        [flags] = binfile.read('I', 4)
        pat0.enabled = flags & 1
        pat0.fixedTexture = flags >> 1 & 1
        # if self.fixedTexture:
        #     print('{} Fixed texture!'.format(self.name))
        pat0.has_texture = flags >> 2 & 1
        pat0.hasPalette = flags >> 3 & 1

    def unpack(self, pat0, binfile):
        binfile.start()
        self.unpack_flags(pat0, binfile)
        [offset] = binfile.read('I', 4)
        binfile.offset = offset + binfile.beginOffset
        self.unpack_frames(pat0, binfile)
        binfile.end()
        return pat0


class UnpackPat0(UnpackSubfile):
    def unpack(self, pat0, binfile):
        super().unpack(pat0, binfile)
        origPathOffset, pat0.framecount, num_mats, num_tex, num_plt, pat0.loop = binfile.read('I4HI', 24)
        if num_plt:
            raise ValueError('Palettes unsupported! Detected palette while parsing')
        assert origPathOffset == 0
        binfile.recall()  # section 0
        folder = Folder(binfile)
        folder.unpack(binfile)
        unpacked = []
        while len(folder):
            name = folder.recallEntryI()
            anim = Pat0MatAnimation(name, pat0.parent, pat0.framecount, pat0.loop)
            unpacked.append(UnpackPat0Animation(anim, binfile))
            pat0.mat_anims.append(anim)
        binfile.recall()  # section 1
        textures = []
        binfile.start()
        for i in range(num_tex):
            textures.append(binfile.unpack_name())
        binfile.end()
        binfile.recall()
        binfile.recall()
        for x in unpacked:
            x.hook_textures(textures)
        binfile.end()
