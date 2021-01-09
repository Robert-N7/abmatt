from copy import deepcopy

from abmatt.brres.lib.binfile import Folder, UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile
from abmatt.brres.srt0.srt0_animation import SRTMatAnim, SRTTexAnim


class UnpackSrt0Tex(Unpacker):
    def unpack_key_frame_list(self, anim, binfile):
        offset = binfile.offset
        binfile.offset = binfile.read('I', 0)[0] + offset
        anim.entries = []
        # header
        size, uk, fs = binfile.read("2Hf", 8)
        # print('FrameScale: {} i v d'.format(fs))
        # str = ''
        if size <= 0:
            raise UnpackingError(binfile, 'SRT0 Key frame list has no entries!')
        for i in range(size):
            index, value, delta = binfile.read("3f", 12)
            # str += '({},{},{}), '.format(index, value, delta)
            anim.entries.append(anim.SRTKeyFrame(value, index, delta))
        binfile.offset = offset + 4
        return anim

    def unpackScale(self, binfile, flags):
        """ unpacks scale data """
        srt0 = self.node
        if flags[0]:
            return
        if flags[3]:  # isotropic
            if flags[4]:  # scale fixed
                [val] = binfile.read("f", 4)
                srt0.animations['xscale'].setFixed(val)
                srt0.animations['yscale'].setFixed(val)
            else:
                keyframelist = self.unpack_key_frame_list(srt0.animations['xscale'], binfile)
                srt0.animations['yscale'] = deepcopy(keyframelist)
        else:  # not isotropic
            if flags[4]:  # xscale-fixed
                [val] = binfile.read("f", 4)
                srt0.animations['xscale'].setFixed(val)
            else:
                self.unpack_key_frame_list(srt0.animations['xscale'], binfile)
            if flags[5]:  # y-scale-fixed
                [val] = binfile.read("f", 4)
                srt0.animations['yscale'].setFixed(val)
            else:
                self.unpack_key_frame_list(srt0.animations['yscale'], binfile)

    def unpackTranslation(self, binfile, flags):
        srt0 = self.node
        """ unpacks translation data """
        if flags[2]:  # default translation
            return
        if flags[7]:  # x-trans-fixed
            [val] = binfile.read("f", 4)
            srt0.animations['xtranslation'].setFixed(val)
        else:
            self.unpack_key_frame_list(srt0.animations['xtranslation'], binfile)
        if flags[8]:  # y-trans-fixed
            [val] = binfile.read("f", 4)
            srt0.animations['ytranslation'].setFixed(val)
        else:
            self.unpack_key_frame_list(srt0.animations['ytranslation'], binfile)

    def unpackRotation(self, binfile, flags):
        """ unpacks rotation """
        if not flags[1]:  # rotation default
            if flags[6]:  # rotation fixed
                [val] = binfile.read("f", 4)
                self.node.animations['rot'].setFixed(val)
            else:
                self.unpack_key_frame_list(self.node.animations['rot'], binfile)

    def parseIntCode(self, code):
        """ Parses the integer code to the class variables """
        code >>= 1
        flags = []
        for i in range(9):
            flags.append(code & 1)
            code >>= 1
        return flags
        # self.scaleDefault = code & 1
        # self.rotationDefault = code >> 1 & 1
        # self.translationDefault = code >> 2 & 1
        # self.scaleIsotropic = code >> 3 & 1
        # self.xScaleFixed = code >> 4 & 1
        # self.yScaleFixed = code >> 5 & 1
        # self.rotationFixed = code >> 6 & 1
        # self.xTranslationFixed = code >> 7 & 1
        # self.yTranslationFixed = code >> 8 & 1

    def unpack(self, srt0, binfile):
        """ unpacks SRT Texture animation data """
        # m = binfile.read('200B', 0)
        # printCollectionHex(m)
        [code] = binfile.read("I", 4)
        flags = self.parseIntCode(code)
        # print('(SRT0){}->{} code:{}'.format(self.parent.name, self.id, code))
        # self.parseIntCode(code)
        self.unpackScale(binfile, flags)
        self.unpackRotation(binfile, flags)
        self.unpackTranslation(binfile, flags)


class UnpackSrt0Material(Unpacker):
    def unpack(self, srt0, binfile):
        """ unpacks the material srt entry """
        offset = binfile.start()
        # data = binfile.read('200B', 0)
        # print('Mat Anim {} at {}'.format(self.name, offset))
        # printCollectionHex(data)
        nameoff, enableFlag, uk = binfile.read("3I", 12)
        bit = 1
        count = 0
        for i in range(8):
            if bit & enableFlag:
                srt0.texEnabled[i] = True
                srt = SRTTexAnim(i, srt0.framecount, srt0)
                srt0.tex_animations.append(srt)
                count += 1
            else:
                srt0.texEnabled[i] = False
            bit <<= 1
        binfile.store(count)  # offsets
        for tex in srt0.tex_animations:
            binfile.recall()
            UnpackSrt0Tex(tex, binfile)
        binfile.end()


class UnpackSrt0(UnpackSubfile):
    def unpack(self, srt0, binfile):
        super().unpack(srt0, binfile)
        uk, srt0.framecount, size, srt0.matrixmode, srt0.loop = binfile.read("I2H2I", 16)
        # advance to section 0
        binfile.recall()
        folder = Folder(binfile, "srt0root")
        folder.unpack(binfile)
        while True:
            e = folder.openI()
            if not e:
                break
            mat = SRTMatAnim(e, srt0.framecount)
            UnpackSrt0Material(mat, binfile)
            srt0.matAnimations.append(mat)
        # binfile.recall()  # section 1 (unknown)
        # self.section1 = binfile.readRemaining(self.byte_len)
        binfile.end()
