#!/usr/bin/python
""" Srt0 Brres subfile """
import math
import re

from ..matching import validInt, validBool, validFloat
from ..subfile import SubFile


# ---------------------------------------------------------

class SRTKeyFrameList:
    ''' Representing an srt non-fixed animation list
        could be scale/rotation/translation
        Always has 1 entry at index 0
    '''
    TYPES = ("xscale", "yscale", "rotation", "xtranslation", "ytranslation")

    class SRTKeyFrame:
        ''' A single animation entry '''

        def __init__(self, value, index=0, delta=0):
            self.index = float(index)  # frame index
            self.value = float(value)  # value
            self.delta = float(delta)  # change per frame

        def __eq__(self, other):
            return self.index == other.index and self.value == other.value and self.delta == other.delta

    def __init__(self, frameCount):
        self.frameCount = frameCount
        self.entries = [self.SRTKeyFrame(0)]

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        return self.entries[key]

    def __setitem__(self, key, value):
        self.setKeyFrame(value, key)

    def __eq__(self, other):
        my_entries = self.entries
        other_entries = other.entries
        if len(my_entries) != len(other_entries):
            return False
        for i in range(len(my_entries)):
            if my_entries[i] != other_entries[i]:
                return False
        return True

    def getFrame(self, i):
        """ Gets frame with index i """
        for x in self.entries:
            if x.index == i:
                return x
        return None

    def getValue(self, index=0):
        """ Gets the value of key frame with frame index"""
        for x in self.entries:
            if x.index == index:
                return x.value

    def calcDelta(self, id1, val1, id2, val2):
        if val1 == val2:  # divide by 0
            return 0
        return (id2 - id1) / (val2 - val1)

    def updateEntry(self, entry_index):
        """Calculates the deltas due to a changed entry"""
        entry = self.entries[entry_index]
        if len(self.entries) < 2:  # one or 0
            entry.delta = 0
        else:
            if entry_index != -1 and entry_index != len(self.entries):
                next = self.entries[entry_index + 1]
                next_id = next.index
            else:
                next = self.entries[0]
                next_id = next.index + self.frameCount
            prev = self.entries[entry_index - 1]
            if entry_index == 0:
                prev_id = prev.index - self.frameCount
            else:
                prev_id = prev.index
            entry.delta = self.calcDelta(entry.index, entry.value, next_id, next.value)
            prev.delta = self.calcDelta(prev_id, prev.value, entry.index, entry.value)

    def setKeyFrame(self, value, index=0):
        """ Adds/sets key frame, overwriting any existing frame at index
            automatically updates delta.
        """
        if not 0 <= index <= self.frameCount:
            raise ValueError("Frame Index {} out of range.".format(index))
        entries = self.entries
        found = False
        for i in range(1, len(entries)):
            cntry = entries[i]
            if index < cntry.index:  # insert
                new_entry = self.SRTKeyFrame(value, index)
                entries.insert(i, new_entry)
                self.updateEntry(i)
                found = True
                break
            elif index == cntry.index:  # replace
                cntry.value = value
                self.updateEntry(i)
                break
        if not found:  # append it
            new_entry = self.SRTKeyFrame(value, index)
            entries.append(new_entry)
            self.updateEntry(-1)

    def removeKeyFrame(self, index):
        """ Removes key frame from list, updating delta """
        entries = self.entries
        for i in range(1, len(entries)):
            if entries[i].index == index:
                prev = entries[i - 1]
                if i == len(entries) - 1:  # last entry?
                    next_entry = entries[0]
                    next_id = self.frameCount
                else:
                    next_entry = entries[i + 1]
                    next_id = next_entry.index
                prev.value = self.calcDelta(prev.index, prev.value, next_id, next_entry.value)
                entries.pop(i)
                break

    def clearFrames(self):
        """ Clears all frames, resetting to one default """
        self.entries = [self.SRTKeyFrame(0)]

    def setFrameCount(self, frameCount):
        """ Sets frame count, removing extra frames """
        e = self.entries
        self.frameCount = frameCount
        for i in range(len(e)):
            if e[i].index > frameCount:
                self.entries = e[:i]  # possibly fix ending delta todo?
                return i
        return 0

    def unpack(self, binfile):
        """ unpacks an animation entry list """
        self.entries = []
        # data = binfile.read('30B', 0)
        # printCollectionHex(data)
        # header
        size, uk, fs = binfile.read("2Hf", 8)
        for i in range(size):
            index, value, delta = binfile.read("3f", 12)
            self.entries.append(self.SRTKeyFrame(value, index, delta))

    def pack(self, binfile, framescale):
        ''' packs an animation entry list '''
        binfile.write("2Hf", len(self.entries), 0, framescale)
        for x in self.entries:
            binfile.write("3f", x.index, x.value, x.delta)


class SRTTexAnim():
    """ A single texture animation entry in srt0 under material """
    SETTINGS = ('lockscaleone', 'lockrotationzero', 'locktranslationzero', 'fixedaspectratio',
                'fixedxscale', 'fixedyscale', 'fixedrotation', 'fixedxtranslation',
                'fixedytranslation', 'keyframe')

    def __init__(self, i, framecount):
        self.id = i
        self.scaleDefault = True  # scale = 1
        self.rotationDefault = True  # rotation = zero
        self.translationDefault = True  # translation = zero
        self.scaleIsotropic = True  # xscale == yscale
        self.xScaleFixed = False
        self.xScale = 1
        self.yScaleFixed = False
        self.yScale = 1
        self.rotationFixed = False
        self.rotation = 0
        self.xTranslationFixed = False
        self.xTranslation = 0
        self.yTranslationFixed = False
        self.yTranslation = 0
        self.animations = {
            'xscale': SRTKeyFrameList(framecount),
            'yscale': SRTKeyFrameList(framecount),
            'rotation': SRTKeyFrameList(framecount),
            'xtranslation': SRTKeyFrameList(framecount),
            'ytranslation': SRTKeyFrameList(framecount)
        }

    # -------------------------------------------------------------------------
    # interfacing
    def __getitem__(self, item):
        if 'keyframe' in item:
            frame_index = re.search("[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?", item)
            if 'xscale' in item:
                return self.animations['xscale'][frame_index]
            elif 'yscale' in item:
                return self.animations['yscale'][frame_index]
            elif 'rotation' in item:
                return self.animations['rotation'][frame_index]
            elif 'xtranslation' in item:
                return self.animations['xtranslation'][frame_index]
            elif 'ytranslation' in item:
                return self.animations['ytranslation'][frame_index]
        else:
            if 'lock' in item:
                if 'scale' in item:
                    return self.scaleDefault
                elif 'rotation' in item:
                    return self.rotationDefault
                elif 'translation' in item:
                    return self.translationDefault
            elif 'fixed' in item:
                if 'xscale' in item:
                    return self.xScale
                elif 'yscale' in item:
                    return self.yScale
                elif 'rotation' in item:
                    return self.rotation
                elif 'xtranslation' in item:
                    return self.xTranslation
                elif 'ytranslation' in item:
                    return self.yTranslation

    def __setitem__(self, key, value):
        if 'keyframe' in key:
            if 'xscale' in key:
                self.animations['xscale'][key] = value
            elif 'yscale' in key:
                self.animations['yscale'][key] = value
            elif 'rotation' in key:
                self.animations['rotation'][key] = value
            elif 'xtranslation' in key:
                self.animations['xtranslation'][key] = value
            elif 'ytranslation' in key:
                self.animations['ytranslation'][key] = value
        else:
            if 'lock' in key:
                val = validBool(value)
                if 'scale' in key:
                    self.scaleDefault = val
                elif 'rotation' in key:
                    self.rotationDefault = val
                elif 'translation' in key:
                    self.translationDefault = val
            elif 'fixed' in key:
                if value == 'none' or value == 'false' or value == 'disable':
                    disable = True
                else:
                    disable = False
                    val = validFloat(value, -math.inf, math.inf)
                if 'xscale' in key:
                    self.xScaleFixed = not disable
                    if self.xScaleFixed:
                        self.xScale = val
                elif 'yscale' in key:
                    self.yScaleFixed = not disable
                    if self.yScaleFixed:
                        self.yScale = val
                elif 'rotation' in key:
                    self.rotationFixed = not disable
                    if self.rotationFixed:
                        self.rotation = val
                elif 'xtranslation' in key:
                    self.xTranslationFixed = not disable
                    if self.xTranslationFixed:
                        self.xTranslation = val
                elif 'ytranslation' in key:
                    self.yTranslationFixed = not disable
                    if self.yTranslationFixed:
                        self.yTranslation = val

    def setKeyFrame(self, animType, value, index=0):
        """ Adds a key frame to the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[animType].setKeyFrame(value, index)

    def removeFrame(self, animType, index):
        ''' Removes a key frame from the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        '''
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[animType].removeKeyFrame(index)

    def clearFrames(self, animType):
        ''' clears frames for an animation type
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        '''
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[i].clearFrames()

    def setFrameCount(self, frameCount):
        ''' Sets the frame count '''
        animations = self.animations
        for x in animations:
            animations[x].setFrameCount(frameCount)

    # ----------------------------------------------------------------------

    # ----------------------------------------------------------------------
    # Code and flags and things
    #       Animation Code Notes
    # //0000 0000 0000 0000 0000 0000 0000 0001       Always set
    #
    # //0000 0000 0000 0000 0000 0000 0000 0010       Scale One
    # //0000 0000 0000 0000 0000 0000 0000 0100       Rot Zero
    # //0000 0000 0000 0000 0000 0000 0000 1000       Trans Zero
    # //0000 0000 0000 0000 0000 0000 0001 0000		Scale Isotropic
    #
    # //0000 0000 0000 0000 0000 0000 0010 0000		Fixed Scale X
    # //0000 0000 0000 0000 0000 0000 0100 0000		Fixed Scale Y
    # //0000 0000 0000 0000 0000 0000 1000 0000		Fixed Rotation
    # //0000 0000 0000 0000 0000 0001 0000 0000		Fixed X Translation
    # //0000 0000 0000 0000 0000 0010 0000 0000		Fixed Y Translation
    def calculateCode(self):
        """ calculates flags based on values"""
        # Scale
        x = self.animations[0]  # XScale
        y = self.animations[1]  # yscale
        self.xScaleFixed = len(x) == 1
        self.yScaleFixed = len(y) == 1
        self.scaleDefault = not x and not y
        if len(x) != len(y):
            self.scaleIsotropic = False
        else:
            self.scaleIsotropic = True
            for i in range(len(x)):
                if x[i].value != y[i].value:
                    self.scaleIsotropic = False
                    break
        # Rotation
        rot = self.animations[2]
        self.rotationFixed = len(rot) == 1
        self.rotationDefault = (rot == False)
        # Translation
        x = self.animations[3]
        y = self.animations[4]
        self.xTranslationFixed = len(x) == 1
        self.yTranslationFixed = len(y) == 1
        self.translationDefault = not x and not y
        return self.flagsToInt()

    def parseIntCode(self, code):
        """ Parses the integer code to the class variables """
        code >>= 1
        self.scaleDefault = code & 1
        self.rotationDefault = code >> 1 & 1
        self.translationDefault = code >> 2 & 1
        self.scaleIsotropic = code >> 3 & 1
        self.xScaleFixed = code >> 4 & 1
        self.yScaleFixed = code >> 5 & 1
        self.rotationFixed = code >> 6 & 1
        self.xTranslationFixed = code >> 7 & 1
        self.yTranslationFixed = code >> 8 & 1

    def flagsToInt(self):
        """ Returns integer from flags """
        return 1 | self.scaleDefault << 1 | self.rotationDefault << 2 | self.translationDefault << 3 \
                 | self.scaleIsotropic << 4 | self.xScaleFixed << 5 | self.yScaleFixed << 6 | self.rotationFixed << 7 \
                 | self.xTranslationFixed << 8 | self.yTranslationFixed << 9

    # -------------------------------------------------------
    # UNPACKING/PACKING
    # probably a better way to do all this
    def unpackScale(self, binfile):
        """ unpacks scale data """
        if self.scaleDefault:
            return
        if self.scaleIsotropic:
            if self.xScaleFixed:
                [val] = binfile.read("f", 4)
                self.xScale = val
                self.yScale = val
            else:
                offset = binfile.offset
                [binfile.offset] = binfile.read("I", 4)
                self.animations['xscale'].unpack(binfile, False)
                self.animations['yscale'].unpack(binfile, False)
                binfile.offset = offset + 4
        else:  # not isotropic
            if self.xScaleFixed:
                [val] = binfile.read("f", 4)
                self.xScale = val
            else:
                binfile.bl_unpack(self.animations['xscale'], False)
            if self.yScaleFixed:
                [val] = binfile.read("f", 4)
                self.yScale = val
            else:
                binfile.bl_unpack(self.animations['yscale'], False)

    def unpackTranslation(self, binfile):
        """ unpacks translation data """
        if self.translationDefault:
            return
        if self.xTranslationFixed:
            [val] = binfile.read("f", 4)
            self.xTranslation = val
        else:
            binfile.bl_unpack(self.animations['xtranslation'], False)
        if self.yTranslationFixed:
            [val] = binfile.read("f", 4)
            self.yTranslation = val
        else:
            binfile.bl_unpack(self.animations['ytranslation'], False)

    def unpackRotation(self, binfile):
        ''' unpacks rotation '''
        if not self.rotationDefault:
            if self.rotationFixed:
                [val] = binfile.read("f", 4)
                self.rotation = val
            else:
                binfile.bl_unpack(self.animations['rotation'])

    def unpack(self, binfile):
        ''' unpacks SRT Texture animation data '''
        # m = binfile.read('200B', 0)
        # printCollectionHex(m)
        [code] = binfile.read("I", 4)
        self.parseIntCode(code)
        self.unpackScale(binfile)
        self.unpackRotation(binfile)
        self.unpackTranslation(binfile)

    def packScale(self, binfile):
        """ packs scale data
            returning a tuple (hasxListOffset, hasyListOffset)
        """
        has_y_list_offset = has_x_list_offset = False
        if not self.scaleDefault:
            if self.xScaleFixed:
                binfile.write("f", self.xScale)
            else:
                binfile.mark()  # mark to be stored
                has_x_list_offset = True
            if not self.scaleIsotropic:
                if self.yScaleFixed:
                    binfile.write("f", self.yScale)
                else:
                    binfile.mark()
                    has_y_list_offset = True
        return [has_x_list_offset, has_y_list_offset]

    def packRotation(self, binfile):
        """ packs rotation data """
        if not self.rotationDefault:
            if self.rotationFixed:
                binfile.write("f", self.rotation)
            else:
                binfile.mark()
                return True
        return False

    def packTranslation(self, binfile):
        """ packs translation data, returning tuple (hasXTransOffset, hasYTransOffset) """
        hasXTransOffset = hasYTransOffset = False
        if not self.translationDefault:
            if self.xTranslationFixed:
                binfile.write("f", self.xTranslation)
            else:
                binfile.mark()
                hasXTransOffset = True
            if self.yTranslationFixed:
                binfile.write("f", self.yTranslation)
            else:
                binfile.mark()
                hasYTransOffset = True
        return [hasXTransOffset, hasYTransOffset]

    def packHead(self, binfile):
        """ packs the texture animation entry,
            returns offset markers to be passed to pack data
            (after packing all headers for material)
        """
        # code = self.calculateCode()
        code = self.flagsToInt()
        binfile.write("I", code)
        have_offsets = self.packScale(binfile)
        have_offsets.append(self.packRotation(binfile))
        have_offsets.extend(self.packTranslation(binfile))
        return have_offsets


class SRTMatAnim():
    """ An entry in the SRT, supports multiple tex refs """

    def __init__(self, name, frame_count=1):
        self.name = name
        self.frameCount = frame_count
        self.tex_animations = []
        self.texEnabled = [False] * 8

    def __getitem__(self, i):
        for x in self.tex_animations:
            if x.id == i:
                return x

    def setFrameCount(self, count):
        self.frameCount = count
        for x in self.tex_animations:
            x.setFrameCount(count)

    def addTexAnimation(self, i):
        if not 0 <= i < 8:
            raise ValueError("Tex Animation {} out of range.".format(i))
        if not self.texEnabled[i]:
            self.texEnabled[i] = True
            self.tex_animations.append(SRTTexAnim(i, self.frameCount))

    def texIsEnabled(self, i):
        return self.texEnabled[i]

    # -----------------------------------------------------
    #  Packing
    def consolidate(self, binfile, has_key_frames):
        """consolidates and packs the frame lists based on the animations that have key frames"""
        frame_lists_offsets = {} # dictionary to track offsets of frame lists
        frame_scale = Srt0.calcFrameScale(self.frameCount)
        for j in range(len(self.tex_animations)):
            has_frames = has_key_frames[j]
            tex = self.tex_animations[j]
            for i in range(len(has_frames)):
                if has_frames[i]:
                    test_list = tex.animations[SRTKeyFrameList.TYPES[i]]
                    found = False
                    for x in frame_lists_offsets:
                        if frame_lists_offsets[x] == test_list:  # move the offset to create the reference.. and move back
                            tmp = binfile.offset
                            binfile.offset = x
                            binfile.createRefFromStored()
                            binfile.offset = tmp
                            found = True
                            break
                    if not found:
                        frame_lists_offsets[binfile.offset] = test_list
                        binfile.createRefFromStored()
                        test_list.pack(binfile, frame_scale)

    def unpack(self, binfile):
        """ unpacks the material srt entry """
        binfile.start()
        nameoff, enableFlag, uk = binfile.read("3I", 12)
        bit = 1
        count = 0
        for i in range(8):
            if bit & enableFlag:
                self.texEnabled[i] = True
                self.tex_animations.append(SRTTexAnim(i, self.frameCount))
                count += 1
            else:
                self.texEnabled.append(False)
            bit <<= 1
        binfile.store(count)  # offsets
        for tex in self.tex_animations:
            binfile.recall()
            tex.unpack(binfile)
        binfile.end()

    def pack(self, binfile, framescale):
        ''' Packs the material srt entry '''
        binfile.start()
        binfile.storeNameRef(self.name)
        # parse enabled
        i = 0
        count = 0
        for x in self.texEnabled:
            i <<= 1
            if x:
                i |= 1
                count += 1
        binfile.write("2I", i, 0)
        binfile.mark(count)
        offsets = []
        animations = self.tex_animations
        for tex in animations:
            binfile.createRef()
            offsets.append(tex.packHead(binfile))
        self.consolidate(binfile, offsets)
        binfile.end()
    # -----------------------------------------------------


class Srt0(SubFile):
    """ Srt0 Animation """
    # todo: clean up this mess, allow setting individual tangent values and defaults etc...
    MAGIC = "SRT0"
    VERSION_SECTIONCOUNT = {4: 1, 5: 2}
    SETTINGS = ("framecount", "looping", "keyframe")

    def __init__(self, name, parent):
        super(Srt0, self).__init__(name, parent)
        self.matAnimations = []
        self.framecount = 1
        self.looping = True

    def __getitem__(self, key):
        if key == 'framecount':
            return self.framecount
        elif key == 'looping':
            return self.looping

    def __setitem__(self, key, value):
        if key == 'framecount':
            i = validInt(value, 1, math.inf)
            self.framecount = i
            for x in self.matAnimations:
                x.setFrameCount(i)
        elif key == 'looping':
            self.looping = validBool(value)
            for x in self.matAnimations:
                x.setLooping(self.looping)

    # ---------------------------------------------------------------------
    # interfacing
    def getMatByName(self, matname):
        """ Gets the material animation by material name """
        for x in self.matAnimations:
            if x.name == matname:
                return x

    def setFrameCount(self, count):
        if count >= 1:
            self.framecount = count
            for x in self.matAnimations:
                x.setFrameCount(count)
        else:
            raise ValueError("Frame count {} is not valid".format(count))

    def addMatAnimation(self, material):
        """ Adds a material animation """
        if self.getMatByName(material.name):
            print("Material {} is already in SRT.".format(material.name))
        # todo - reference material to animation?
        else:
            self.matAnimations.append(SRTMatAnim(material.name, self.framecount))

    def removeMatAnimation(self, material):
        """ Removes a material animation """
        ma = self.matAnimations
        for i in range(len(ma)):
            if ma[i].name == material.name:
                return ma.pop(i)
        return None

    def setLooping(self, val):
        self.looping = val

    @staticmethod
    def calcFrameScale(frameCount):
        """ calculates the frame scale... 1/framecount """
        return 1 / frameCount if frameCount > 1 else 1

    # ----------------------------------------------------------------------
    #   PACKING
    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)
        return
        # uk, self.framecount, self.size, self.matrixmode, self.looping = binfile.read("I2H2I", 16)
        # # advance to section 0
        # binfile.recall()
        # folder = Folder(binfile, "scn0root")  # todo name here
        # folder.unpack(binfile)
        # while True:
        #     e = folder.openI()
        #     if not e:
        #         break
        #     mat = SRTMatAnim(e, self.framecount)
        #     mat.unpack(binfile)
        #     self.matAnimations.append(mat)
        # binfile.recall()  # section 1 (unknown)
        # self.section1 = binfile.readRemaining(self.byte_len)
        # binfile.end()

    def pack(self, binfile):
        """ Packs the data for SRT file """
        self._pack(binfile)
        self._packData(binfile)
        # binfile.write("I2H2I", 0, self.framecount, len(self.matAnimations),
        #               self.matrixmode, self.looping)
        # binfile.createRef()  # create ref to section 0
        # # create index group
        # folder = Folder(binfile, "scn0root")
        # for x in self.matAnimations:
        #     folder.addEntry(x.name)
        # folder.pack(binfile)
        # framescale = self.calcFrameScale(self.framecount)
        # for x in self.matAnimations:
        #     folder.createEntryRefI()
        #     x.pack(binfile, framescale)
        # binfile.createRef()  # section 1 (unknown)
        # binfile.writeRemaining(self.section1)
        # binfile.end()
