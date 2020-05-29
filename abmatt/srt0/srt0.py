#!/usr/bin/python
''' Srt0 Brres subfile '''
from matching import validInt, validBool
from subfile import SubFile
from binfile import Folder
import math

# ---------------------------------------------------------

class SRTKeyFrameList:
    ''' Representing an srt non-fixed animation list
        could be scale/rotation/translation
        Always has 1 entry at index 0
    '''
    TYPES = ("xscale", "yscale", "rotation", "xtranslation", "ytranslation")
    DEFAULTS = (1, 1, 0, 0, 0)

    class SRTKeyFrame:
        ''' A single animation entry '''
        def __init__(self, value, index = 0, delta = 0):
            self.index = index          # frame index
            self.value = value          # value
            self.delta = delta          # change per frame

        def calcDelta(self, entry):
            ''' Guesses delta between frames to make smooth transition '''
            self.delta = (self.index - entry.index) / (self.value - entry.value)

    def __init__(self, ltype, frameCount):
        self.ltype = ltype
        self.frameCount = frameCount
        i = self.TYPES.index(ltype)
        self.entries = [self.SRTKeyFrame(self.DEFAULTS[i])]

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        return self.entries[key]

    def getFrame(self, i):
        ''' Gets frame with index i '''
        for x in self.entries:
            if x.index == i:
                return x
        return None

    def __bool__(self):
        ''' Returns true if it's not default '''
        if len(self.entries) > 1:
            return True
        i = self.TYPES.index(self.ltype)
        return self.getValue() != self.DEFAULTS[i]

    def getValue(self, index = 0):
        ''' Gets the value of key frame with frame index'''
        for x in self.entries:
            if x.index == index:
                return x.value

    def setKeyFrame(self, value, index):
        ''' Adds/sets key frame, overwriting any existing frame at index
            automatically updates delta.
        '''
        if not 1 <= index <= self.frameCount:
            raise ValueError("Frame Index {} out of range.".format(index))
        entries = self.entries
        found = False
        for i in range(1, len(entries)):
            cntry = entries[i]
            if index < cntry.index:     # insert
                newEntry = self.SRTKeyFrame(value, index)
                entries.insert(i, newEntry)
                entries[i - 1].calcDelta(newEntry)
                newEntry.calcDelta(cntry)
                found = True
                break
            elif index == cntry.index:   # replace
                cntry.value = value
                break
        if not found:   # append it
            newEntry = self.SRTKeyFrame(value, index)
            entries[-1].calcDelta(newEntry)
            entries.append(newEntry)
            next = entries[0]
            # if it's at the end.. set it to be the same as the start
            if newEntry.index == self.frameCount:
                newEntry.delta = next.delta
            else: # calc delta using first value as last index
                next.index = self.frameCount
                newEntry.calcDelta(next)
                next.index = 0

    def removeKeyFrame(self, index = -1):
        ''' Removes key frame from list, updating delta '''
        entries = self.entries
        for i in range(1, len(entries)):
            if entries[i].index == index:
                entries.pop(i)
                if i == len(entries) - 1: # last entry?
                    next = entries[0]
                    next.index = self.frameCount
                    entries[i - 1].calcDelta(next)
                    next.index = 0
                else:
                    entries[i - 1].calcDelta(entries[i])
                break

    def clearFrames(self):
        ''' Clears all frames, resetting to one default '''
        defaultI = self.TYPES.index(self.ltype)
        self.entries = [self.SRTKeyFrame(self.DEFAULTS[defaultI])]

    def setFrameCount(self, frameCount):
        ''' Sets frame count, removing extra frames '''
        e = self.entries
        self.frameCount = frameCount
        for i in range(len(e)):
            if e[i].index > frameCount:
                self.entries = e[:i]    # possibly fix ending delta todo?
                return i
        return 0

    def calcFrameScale(self, frameCount):
        ''' calculates the frame scale... 1/framecount '''
        return 1 / frameCount if frameCount > 1 else 1

    def unpack(self, binfile):
        ''' unpacks an animation entry list '''
        self.entries = []
        # header
        size, uk, fs = binfile.read("2Hf", 8)
        for i in range(size):
            self.entries.append(self.SRTKeyFrame(binfile.read("3f", 12)))

    def pack(self, binfile, framescale):
        ''' packs an animation entry list '''
        binfile.write("2Hf", len(self.entries), 0, framescale)
        for x in self.entries:
            binfile.write("3f", x.index, x.value, x.delta)


class  SRTTexAnim():
    ''' A single texture animation entry in srt0 under material '''

    def __init__(self, i, framecount):
        self.id = i
        self.scaleDefault = True            # scale = 1
        self.rotationDefault = True         # rotation = zero
        self.translationDefault = True      # translation = zero
        self.scaleIsotropic = True          # xscale == yscale
        self.xScaleFixed = False
        self.yScaleFixed = False
        self.rotationFixed = False
        self.xTranslationFixed = False
        self.yTranslationFixed = False
        self.flags = [self.scaleDefault, self.rotationDefault, self.translationDefault,
                     self.scaleIsotropic, self.xScaleFixed, self.yScaleFixed,
                     self.rotationFixed, self.xTranslationFixed, self.yTranslationFixed]
        self.animations = []
        for ltype in SRTKeyFrameList.TYPES:
            self.animations.append(SRTKeyFrameList(ltype, framecount))

    # -------------------------------------------------------------------------
    # interfacing
    def setKeyFrame(self, animType, value, index):
        ''' Adds a key frame to the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        '''
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[i].setKeyFrame(value, index)

    def removeFrame(self, animType, index):
        ''' Removes a key frame from the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        '''
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[i].removeKeyFrame(index)

    def clearFrames(self, animType):
        ''' clears frames for an animation type
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        '''
        i = SRTKeyFrameList.TYPES.index(animType)
        return self.animations[i].clearFrames()

    def setFrameCount(self, frameCount):
        ''' Sets the frame count '''
        for x in self.animations:
            x.setFrameCount(frameCount)

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
        ''' calculates flags based on values'''
        # Scale
        x = self.animations[0] # XScale
        y = self.animations[1] # yscale
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
        ''' Parses the integer code to the class variables '''
        bit = 1
        for flag in self.flags:
            bit <<= 1
            flag = bit & code

    def flagsToInt(self):
        ''' Returns integer from flags '''
        x = 1
        bit = 1
        for flag in self.flags:
            bit <<= 1
            x |= flag & bit
        return x

    def getArgCount(self):
        ''' gets the number of arguments based on current flags (either float or offset)'''
        count = 0
        if not self.flags[0]:   # scale != 1 so has value
            count = 1 if self.flags[3] else 2   # 1 if isotropic
        if not self.flags[1]:
            count += 1
        if not self.flags[2]:
            count += 1
        return count

    # -------------------------------------------------------
    # UNPACKING/PACKING
    # probably a better way to do all this
    def unpackScale(self, binfile):
        ''' unpacks scale data '''
        if self.scaleDefault:
            return
        if self.scaleIsotropic:
            if self.xScaleFixed:
                [val] = binfile.read("f", 4)
                self.animations[0].setValue(val)
                self.animations[1].setValue(val)
            else:
                offset = binfile.offset
                [binfile.offset] = binfile.read("I", 4)
                self.animations[0].unpack(binfile)
                self.animations[1].unpack(binfile)
                binfile.offset = offset + 4
        else:   # not isotropic
            if self.xScaleFixed:
                [val] = binfile.read("f", 4)
                self.animations[0].setValue(val)
            else:
                binfile.bl_unpack(self.animations[0], False)
            if self.yScaleFixed:
                [val] = binfile.read("f", 4)
                self.animations[1].setValue(val)
            else:
                binfile.bl_unpack(self.animations[1], False)

    def unpackTranslation(self, binfile):
        ''' unpacks translation data '''
        if self.translationDefault:
            return
        if self.xTranslationFixed:
            [val] = binfile.read("f", 4)
            self.animations[3].setValue(val)
        else:
            binfile.bl_unpack(self.animations[3], False)
        if self.yTranslationFixed:
            [val] = binfile.read("f", 4)
            self.animations[4].setValue(val)
        else:
            binfile.bl_unpack(self.animations[4], False)

    def unpackRotation(self, binfile):
        ''' unpacks rotation '''
        if not self.rotationDefault:
            if self.rotationFixed:
                [val] = binfile.read("f", 4)
                self.animations[2].setValue(val)
            else:
                binfile.bl_unpack(self.animations[2], False)

    def unpack(self, binfile):
        ''' unpacks SRT Texture animation data '''
        [code] = binfile.read("I", 4)
        self.parseIntCode(code)
        self.unpackScale(binfile)
        self.unpackRotation(binfile)
        self.unpackTranslation(binfile)

    def packScale(self, binfile):
        ''' packs scale data
            returning a tuple (hasxListOffset, hasyListOffset)
        '''
        hasyListOffset = hasxListOffset = False
        if not self.scaleDefault:
            x = self.animations["xscale"]
            y = self.animations["yscale"]
            if self.xScaleFixed:
                binfile.write("f", x.getValue())
            else:
                binfile.mark()  # mark to be stored
                hasxListOffset = True
            if not self.scaleIsotropic:
                if self.yScaleFixed:
                    binfile.write("f", y.getValue())
                else:
                    binfile.mark()
                    hasyListOffset = True
        return (hasxListOffset, hasyListOffset)

    def packRotation(self, binfile):
        ''' packs rotation data '''
        if not self.rotationDefault:
            if self.rotationFixed:
                binfile.write("f", self.animations["rotation"].getValue())
            else:
                binfile.mark()
                return True
        return False

    def packTranslation(self, binfile):
        ''' packs translation data, returning tuple (hasXTransOffset, hasYTransOffset) '''
        hasXTransOffset = hasYTransOffset = False
        if not self.translationDefault:
            if self.xTranslationFixed:
                binfile.write("f", self.animations["xtranslation"].getValue())
            else:
                binfile.mark()
                hasXTransOffset = True
            if self.yTranslationFixed:
                binfile.write("f", self.animations["ytranslation"].getValue())
            else:
                binfile.mark()
                hasYTransOffset = False
        return (hasXTransOffset, hasYTransOffset)

    def pack(self, binfile, framescale):
        ''' packs the texture animation entry '''
        code = self.calculateCode()
        binfile.write("I", code)
        haveOffsets = self.packScale(binfile)
        haveOffsets.append( self.packRotation(binfile))
        haveOffsets.extend(list(self.packTranslation(binfile)))
        for i in range(len(haveOffsets)):
            if haveOffsets[i]: # then pack key frames
                binfile.createRefFromStored()
                self.animations[i].pack(binfile, framescale)
                if i == 0 and self.scaleIsotropic: # special case for isotropic
                    self.animations[i + 1].pack(binfile, framescale)


class SRTMatAnim():
    ''' An entry in the SRT, supports multiple tex refs '''
    def __init__(self, name, framecount = 1):
        self.name = name
        self.frameCount = framecount
        self.texAnim = []
        self.texEnabled = [False] * 8

    def __getitem__(self, i):
        for x in self.texAnim:
            if x.id == i:
                return x

    def setFrameCount(self, count):
        self.frameCount = count
        for x in self.texAnim:
            x.setFrameCount(count)

    def addTexAnimation(self, i):
        if not 0 <= i < 8:
            raise ValueError("Tex Animation {} out of range.".format(i))
        if not self.texEnabled[i]:
            self.texEnabled[i] = True
            self.texAnim.append(SRTTexAnim(i, self.frameCount))

    def texIsEnabled(self, i):
        return self.texEnabled[i]

    # -----------------------------------------------------
    #  Packing
    def unpack(self, binfile):
        ''' unpacks the material srt entry '''
        binfile.start()
        nameoff, self.enableFlag, uk = binfile.read("3I", 12)
        bit = 1
        self.count = 0
        for i in range(8):
            if bit & self.enableFlag:
                self.texEnabled[i] = True
                self.texAnim.append(SRTTexAnim(i, self.frameCount))
                self.count+=1
            else:
                self.texEnabled.append(False)
            bit <<= 1
        binfile.store(self.count)   # offsets
        for tex in self.texAnim:
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
                count +=  1
        binfile.write("2I", i, 0)
        binfile.mark(count)
        for tex in self.texAnim:
            binfile.createRef()
            tex.pack(binfile, framescale)
        binfile.end()
    # -----------------------------------------------------


class Srt0(SubFile):
    ''' Srt0 Animation '''
    MAGIC = "SRT0"
    VERSION_SECTIONCOUNT = {4:1, 5:2}
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
        elif key == 'looping':
            self.looping = validBool(value)
            for x in self.matAnimations:
                x.setLooping(self.looping)

    # ---------------------------------------------------------------------
    # interfacing
    def getMatByName(self, matname):
        ''' Gets the material animation by material name '''
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
        ''' Adds a material animation '''
        if self.getMatByName(material.name):
            print("Material {} is already in SRT.".format(material.name))
        # todo - reference material to animation?
        else:
            self.matAnimations.append(SRTMatAnim(material.name, self.framecount))

    def removeMatAnimation(self, material):
        ''' Removes a material animation '''
        ma = self.matAnimations
        for i in range(len(ma)):
            if ma[i].name == material.name:
                return ma.pop(i)
        return None

    def setLooping(self, val):
        self.looping = val

    # ----------------------------------------------------------------------
    #   PACKING
    def unpack(self, binfile):
        self._unpack(binfile)
        uk, self.framecount, self.size, self.matrixmode, self.looping = binfile.read("I2H2I", 16)
        # advance to section 0
        binfile.recall()
        folder = Folder(binfile, "scn0root") # todo name here
        folder.unpack(binfile)
        while True:
            e = folder.openI()
            if not e:
                break
            mat = SRTMatAnim(e)
            mat.unpack(binfile)
            self.matAnimations.append(mat)
        binfile.recall() # section 1 (unknown)
        self.section1 = binfile.readRemaining(self.len)
        binfile.end()

    def pack(self, binfile):
        self._pack(binfile)
        ''' Packs the data for SRT file '''
        binfile.write("I2H2I", 0, self.framecount, len(self.matAnimations),
                  self.matrixmode, self.looping)
        binfile.createRef()  # create ref to section 0
        # create index group
        folder = Folder(binfile, "scn0root")
        for x in self.matAnimations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        framescale = SRTKeyFrameList.calcFrameScale(self.framecount)
        for x in self.matAnimations:
            folder.createEntryRefI()
            x.pack(binfile, framescale)
        binfile.createRef() # section 1 (unknown)
        binfile.writeRemaining(self.section1)
