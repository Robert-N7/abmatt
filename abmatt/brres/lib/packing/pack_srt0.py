from brres.lib.binfile import Folder
from brres.lib.packing.interface import Packer
from brres.lib.packing.pack_subfile import PackSubfile
from brres.srt0.srt0_animation import SRTTexAnim


def calcFrameScale(frameCount):
    """ calculates the frame scale... 1/framecount """
    return 1.0 / frameCount if frameCount > 1 else 1


class PackSrt0Tex(Packer):
    def __init__(self, node, binfile):
        self.has_offsets = [False] * 5
        super().__init__(node, binfile)

    def packScale(self, binfile, flags):
        """ packs scale data
            returning a tuple (hasxListOffset, hasyListOffset)
        """
        if not flags[0]:    # not scale default
            if flags[4]:    # x-scale-fixed
                binfile.write("f", self.node.animations['xscale'].getValue())
            else:
                binfile.mark()  # mark to be stored
                self.has_offsets[0] = True
            if not flags[3]:    # not isotropic
                if flags[5]:    # y-scale-fixed
                    binfile.write("f", self.node.animations['yscale'].getValue())
                else:
                    binfile.mark()
                    self.has_offsets[1] = True

    def packRotation(self, binfile, flags):
        """ packs rotation data """
        if not flags[1]:    # rotation not default
            if flags[6]:    # rotation fixed
                binfile.write("f", self.node.animations['rot'].getValue())
            else:
                binfile.mark()
                self.has_offsets[2] = True

    def packTranslation(self, binfile, flags):
        """ packs translation data, returning tuple (hasXTransOffset, hasYTransOffset) """
        if not flags[2]:    # not trans-default
            if flags[7]:    # x-trans
                binfile.write("f", self.node.animations['xtranslation'].getValue())
            else:
                binfile.mark()
                self.has_offsets[3] = True
            if flags[8]:    # y-trans
                binfile.write("f", self.node.animations['ytranslation'].getValue())
            else:
                binfile.mark()
                self.has_offsets[4] = True

    def flagsToInt(self, flags):
        """ Returns integer from flags """
        code = 0
        for i in range(len(flags)):
            code |= flags[i] << i
        code = code << 1 | 1
        return code

    def calc_flags(self):
        """ calculates flags based on values"""
        srt0 = self.node
        flags = [False] * 9
        # Scale
        x = srt0.animations['xscale']  # XScale
        y = srt0.animations['yscale']  # yscale
        flags[4] = x.isFixed()
        flags[5] = y.isFixed()
        flags[0] = (x.isDefault(True) and y.isDefault(True))
        flags[3] = flags[0] or x == y
        # Rotation
        rot = srt0.animations['rot']
        flags[6] = rot.isFixed()
        flags[1] = rot.isDefault(False)
        # Translation
        x = srt0.animations['xtranslation']
        y = srt0.animations['ytranslation']
        flags[7] = x.isFixed()
        flags[8] = y.isFixed()
        flags[2] = x.isDefault(False) and y.isDefault(False)
        return flags

    def pack(self, srt0, binfile):
        """ packs the texture animation entry,
            returns offset markers to be passed to pack data
            (after packing all headers for material)
        """
        flags = self.calc_flags()
        binfile.write("I", self.flagsToInt(flags))
        self.packScale(binfile, flags)
        self.packRotation(binfile, flags)
        self.packTranslation(binfile, flags)
        return self.has_offsets


class PackSrt0Material(Packer):
    def __init__(self, node, binfile):
        self.has_key_frames = []
        super().__init__(node, binfile)

    def pack_key_frame_list(self, binfile, anim, framescale):
        binfile.write("2Hf", len(anim.entries), 0, framescale)
        for x in anim.entries:
            binfile.write("3f", x.index, x.value, x.delta)

    def consolidate(self, binfile, frame_lists_offsets):
        """consolidates and packs the frame lists based on the animations that have key frames"""
        srt0 = self.node
        frame_scale = calcFrameScale(srt0.framecount)
        for j in range(len(self.has_key_frames)):  # Each texture
            has_frames = self.has_key_frames[j]
            tex = srt0.tex_animations[j]
            for i in range(len(has_frames)):  # srt
                if has_frames[i]:
                    test_list = tex.animations[SRTTexAnim.SETTINGS[i]]
                    found = False
                    for x in frame_lists_offsets:
                        if frame_lists_offsets[x] == test_list:  # move the offset to create the reference and move back
                            tmp = binfile.offset
                            binfile.offset = x
                            binfile.createRefFromStored(0, True, self.offset)
                            binfile.offset = tmp
                            found = True
                            break
                    if not found:
                        frame_lists_offsets[binfile.offset] = test_list
                        binfile.createRefFromStored(0, True, self.offset)
                        self.pack_key_frame_list(binfile, test_list, frame_scale)

    def pack(self, srt0, binfile):
        """ Packs the material srt entry """
        self.offset = binfile.start()
        binfile.storeNameRef(srt0.name)
        # parse enabled
        i = count = 0
        bit = 1
        for x in srt0.texEnabled:
            if x:
                i |= bit
                count += 1
            bit <<= 1
        binfile.write("2I", i, 0)
        binfile.mark(count)
        animations = srt0.tex_animations
        for tex in animations:
            binfile.createRef()
            p = PackSrt0Tex(tex, binfile)
            self.has_key_frames.append(p.has_offsets)
        binfile.end()


class PackSrt0(PackSubfile):

    def pack(self, srt0, binfile):
        """ Packs the data for SRT file """
        super().pack(srt0, binfile)
        binfile.write("I2H2I", 0, srt0.framecount, len(srt0.matAnimations),
                      srt0.matrixmode, srt0.loop)
        binfile.createRef()  # create ref to section 0
        # create index group
        folder = Folder(binfile, "srt0root")
        for x in srt0.matAnimations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        packers = []
        for x in srt0.matAnimations:
            folder.createEntryRefI()
            packers.append(PackSrt0Material(x, binfile))
        # Now for key frames
        key_frame_lists = {}  # map of offsets to frame lists
        for x in packers:
            x.consolidate(binfile, key_frame_lists)
        # binfile.createRef()  # section 1 (unknown)
        # binfile.writeRemaining(self.section1)
        binfile.end()
