"""PAT0 Animations"""
from abmatt.subfile import SubFile


class MatAnimation:
    """Single material animation"""

    def __init__(self, name, parent):
        # Flags 0x5
        self.uk0 = 0x19
        self.uk1 = 0
        self.uk2 = 0
        self.uk3 = 1
        self.enabled = True
        self.fixedTexture = False
        self.hasTexture = True
        self.hasPalette = False
        self.scale_factor = 10
        self.frames = []
        self.name = name
        self.parent = parent

    class Frame:
        def __init__(self, frame_id, texture_id, palette_id=0):
            self.frame_id = frame_id
            self.texture_id = texture_id
            self.palette_id = palette_id

    def unpack_frames(self, binfile):
        # frame header
        size, _, self.scale_factor = binfile.read('2Hf', 8)
        frames = self.frames
        for i in range(size):
            frame_id, tex_id, plt_id = binfile.read('f2H', 8)
            frames.append(self.Frame(frame_id, tex_id, plt_id))

    def pack_frames(self, binfile):
        frames = self.frames
        binfile.write('2Hf', len(frames), 0, self.scale_factor)
        for x in frames:
            binfile.write('f2H', x.frame_id, x.texture_id, x.palette_id)

    def pack_flags(self, binfile):
        binfile.createRef()  # from the base header
        offset = binfile.start()
        binfile.storeNameRef(self.name)
        flags = self.enabled | self.fixedTexture << 1 | self.hasTexture << 2 | self.hasPalette << 3
        binfile.write('I', flags)
        binfile.mark()
        binfile.end()
        return offset

    def pack(self, binfile):
        binfile.write('4H', self.uk0, self.uk1, self.uk2, self.uk3)
        binfile.storeNameRef(self.name)
        binfile.mark()

    def unpack_flags(self, binfile):
        binfile.start()
        binfile.advance(4)  # already have name
        [flags] = binfile.read('I', 4)
        self.enabled = flags & 1
        self.fixedTexture = flags >> 1 & 1
        self.hasTexture = flags >> 2 & 1
        self.hasPalette = flags >> 3 & 1
        binfile.bl_unpack(self.unpack_frames)
        binfile.end()

    def unpack(self, binfile):
        self.uk0, self.uk1, self.uk2, self.uk3 = binfile.read('4H', 8)
        self.name = binfile.unpack_name()
        binfile.bl_unpack(self.unpack_flags)
        return self


class Pat0(SubFile):
    """ Pat0 animation class """

    MAGIC = "PAT0"
    # Sections:
    #   0: data
    #   1: texture Table
    #   2: palette Table
    #   3: texture ptr Table
    #   4: palette ptr Table
    #   5: user data
    VERSION_SECTIONCOUNT = {3: 5, 4: 6}

    def __init__(self, name, parent):
        super(Pat0, self).__init__(name, parent)
        self.frame_count = 2
        self.loop = True
        self.num_entries = 1
        self.n_str = 1
        self.mat_anims = []
        self.textures = []

    def unpack_matAnim(self, binfile):
        binfile.start()
        header_size, _, num_anims, _, _, self.n_unknown, _, _, _ = binfile.read('I6H2I', 24)
        for i in range(num_anims):  # mat animations
            self.mat_anims.append(MatAnimation(None, self).unpack(binfile))
        binfile.end()

    def pack_matAnim(self, binfile):
        binfile.start()
        animations = self.mat_anims
        length = len(animations)
        header_size = 0x18 + length * 0x10
        binfile.write('I6H2I', header_size, 0, length, 0xffff, 0, self.n_unknown, 0, 0, 0)
        offsets = []  # tracking offsets
        for x in animations:  # indexing
            x.pack(binfile)
        for x in animations:  # flags
            offsets.append(x.pack_flags(binfile))
        for i in range(length):  # frames
            binfile.createRefFrom(offsets[i])
            animations[i].pack_frames(binfile)
        binfile.end()

    def unpack(self, binfile):
        self._unpack(binfile)
        origPathOffset, self.frame_count, self.num_mats, num_tex, num_plt, self.loop = binfile.read('I4HI', 24)
        if num_plt:
            raise ValueError('Palettes unsupported! Detected palette while parsing')
        assert (origPathOffset == 0)
        binfile.recall()  # section 0
        self.unpack_matAnim(binfile)
        binfile.recall()
        binfile.start()
        for i in range(num_tex):
            self.textures.append(binfile.unpack_name())
        binfile.end()
        # remaining = binfile.readRemaining(self.byte_len)
        # printCollectionHex(remaining)
        # ignore the rest
        # binfile.recall()    # section 2: palette
        # binfile.recall()    # section 3: texture ptr table
        # binfile.recall()    # section 4: palette ptr table
        # binfile.recall()    # section 5: user data
        binfile.end()

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I4HI', 0, self.frame_count, self.num_mats, len(self.textures), 0, self.loop)
        binfile.createRef(0, False)  # section 0: data
        self.pack_matAnim(binfile)
        binfile.createRef(1, False)  # section 1: textures
        binfile.start()
        for x in self.textures:
            binfile.storeNameRef(x)
        binfile.end()
        # skip palettes
        binfile.createRef(3, False)  # section 3: bunch of null
        binfile.advance(len(self.textures) * 4)
        # skip palettes/userdata
        # binfile.align()
        binfile.end()
