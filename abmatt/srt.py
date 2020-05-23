#!/usr/bin/python
''' Srt0 Brres subfile '''
from subfile import SubFile

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
        return self.animations[i].addKeyFrame(value, index)

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
    def unpackScale(self, bin):
        ''' unpacks scale data '''
        if self.scaleDefault:
            return
        if self.scaleIsotropic:
            if self.xScaleFixed:
                [val] = bin.read("f", 4)
                self.animations[0].setValue(val)
                self.animations[1].setValue(val)
            else:
                offset = bin.offset
                [bin.offset] = bin.read("I", 4)
                self.animations[0].unpack(bin)
                self.animations[1].unpack(bin)
                bin.offset = offset + 4
        else:   # not isotropic
            if self.xScaleFixed:
                [val] = bin.read("f", 4)
                self.animations[0].setValue(val)
            else:
                bin.bl_unpack(self.animations[0], False)
            if self.yScaleFixed:
                [val] = bin.read("f", 4)
                self.animations[1].setValue(val)
            else:
                bin.bl_unpack(self.animations[1], False)

    def unpackTranslation(self, bin):
        ''' unpacks translation data '''
        if self.translationDefault:
            return
        if self.xTranslationFixed:
            [val] = bin.read("f", 4)
            self.animations[3].setValue(val)
        else:
            bin.bl_unpack(self.animations[3], False)
        if self.yTranslationFixed:
            [val] = bin.read("f", 4)
            self.animations[4].setValue(val)
        else:
            bin.bl_unpack(self.animations[4], False)

    def unpackRotation(self, bin):
        ''' unpacks rotation '''
        if not self.rotationDefault:
            if self.rotationFixed:
                [val] = bin.read("f", 4)
                self.animations[2].setValue(val)
            else:
                bin.bl_unpack(self.animations[2], False)

    def unpack(self, bin):
        ''' unpacks SRT Texture animation data '''
        code = bin.read("I", 4)
        self.parseIntCode(code)
        self.unpackScale(bin)
        self.unpackRotation(bin)
        self.unpackTranslation(bin)

    def packScale(self, bin):
        ''' packs scale data
            returning a tuple (hasxListOffset, hasyListOffset)
        '''
        hasyListOffset = hasxListOffset = False
        if not self.scaleDefault:
            x = self.animations["xscale"]
            y = self.animations["yscale"]
            if self.xScaleFixed:
                bin.write("f", 4, x.getValue())
            else:
                bin.mark()  # mark to be stored
                hasxListOffset = True
            if not self.scaleIsotropic:
                if self.yScaleFixed:
                    bin.write("f", 4, y.getValue())
                else:
                    bin.mark()
                    hasyListOffset = True
        return (hasxListOffset, hasyListOffset)

    def packRotation(self, bin):
        ''' packs rotation data '''
        if not self.rotationDefault:
            if self.rotationFixed:
                bin.write("f", 4, self.animations["rotation"].getValue())
            else:
                bin.mark()
                return True
        return False

    def packTranslation(self, bin):
        ''' packs translation data, returning tuple (hasXTransOffset, hasYTransOffset) '''
        hasXTransOffset = hasYTransOffset = False
        if not self.translationDefault:
            if self.xTranslationFixed:
                bin.write("f", 4, self.animations["xtranslation"].getValue())
            else:
                bin.mark()
                hasXTransOffset = True
            if self.yTranslationFixed:
                bin.write("f", 4, self.animations["ytranslation"].getValue())
            else:
                bin.mark()
                hasYTransOffset = False
        return (hasXTransOffset, hasYTransOffset)

    def pack(self, bin):
        ''' packs the texture animation entry '''
        code = self.calculateCode()
        bin.write("I", 4, code)
        haveOffsets = self.packScale(bin)
        haveOffsets.append( self.packRotation(bin))
        haveOffsets.extend(list(self.packTranslation(bin)))
        for i in range(len(haveOffsets)):
            if haveOffsets[i]: # then pack key frames
                bin.createRefFromStored()
                self.animations[i].pack(bin, framescale)
                if i == 0 and self.scaleIsotropic: # special case for isotropic
                    self.animations[i + 1].pack(bin)

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
            self.entries = [SRTKeyFrame(self.DEFAULTS[i])]

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
            for i in range(1:len(entries)):
                cntry = entries[i]
                if index < cntry.index:     # insert
                    newEntry = SRTKeyFrame(value, index)
                    entries.insert(i, newEntry)
                    entries[i - 1].calcDelta(newEntry)
                    newEntry.calcDelta(cntry)
                    found = True
                    break
                elif index == cntry.index   # replace
                    cntry.value = value
                    break
            if not found:   # append it
                newEntry = SRTKeyFrame(value, index)
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
            for i in range(1:len(entries)):
                if entries[i].index = index:
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
            self.entries = [SRTKeyFrame(self.DEFAULTS[defaultI])]

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
            self.frameScale = 1 / frameCount if frameCount > 1 else 1

        def unpack(self, bin):
            ''' unpacks an animation entry list '''
            self.entries = []
            # header
            size, uk, fs = bin.read("2Hf", 8)
            for i in range(self.size):
                self.entries.append(SRTKeyFrame(bin.read("3f", 12)))

        def pack(self, bin):
            ''' packs an animation entry list '''
            bin.write("2Hf", 8, len(self.entries), 0, self.calcFrameScale(self.frameCount))
            for x in self.entries:
                bin.write("3f", 12, x.index, x.value, x.delta)


class Srt(SubFile):
    ''' Srt0 Animation '''
    MAGIC = "SRT0"
    VERSION_SECTIONCOUNT = {4:1, 5:2}

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.matAnimations = []

    def __getitem__(self, matname):
        ''' Gets the material animation by material name '''
        for x in self.matAnimations:
            if x.name == matname:
                return x

    # ---------------------------------------------------------------------
    # interfacing
    def setFrameCount(self, count):
        if count >= 1:
            self.framecount = count
            for x in self.matAnimations:
                x.setFrameCount(count)
        else:
            raise ValueError("Frame count {} is not valid".format(count))

    def addMatAnimation(self, material):
        ''' Adds a material animation '''
        if self[material.name]:
            print("Material {} is already in SRT.".format(material.name))
        # todo - reference material to animation?
        else:
            self.matAnimations.append(SRTMatAnim(material.name, self.framecount))

    def removeMatAnimation(self, material):
        ''' Removes a material animation '''
        ma = self.matAnimations
        for i in range(len(ma)):
            if ma.name == material.name:
                return ma.pop(i)
        return None

    def setLooping(self, val):
        self.looping = val

    # ----------------------------------------------------------------------
    #   PACKING
    def unpackData(self, bin):
        uk, self.framecount, self.size, self.matrixmode, self.looping = bin.read("I2H2I", 16)
        # advance to section 0
        bin.recall()
        folder = Folder(bin, self, "scn0root") # todo name here
        folder.unpack(bin)
        while True:
            e = folder.openI()
            if not e:
                break
            mat = SRTMatAnim(e)
            mat.unpack(bin)
            self.matAnimations.append(mat)
        bin.recall() # section 1 (unknown)
        self.section1 = bin.readRemaining(self.len)

    def packData(self, bin):
        ''' Packs the data for SRT file '''
        bin.write("I2H2I", 16, 0, self.framecount, len(self.matAnimations),
                  self.matrixmode, self.looping)
        bin.createRef()  # create ref to section 0
        # create index group
        folder = Folder(bin, self, "scn0root")
        for x in self.matAnimations:
            folder.addEntry(x.name)
        folder.pack(bin)
        for x in self.matAnimations:
            folder.createEntryRefI()
            x.pack(bin)
        bin.createRef() # section 1 (unknown)
        bin.writeRemaining(self.section1)


    class SRTMatAnim():
        ''' An entry in the SRT, supports multiple tex refs '''
        def __init__(self, name, framecount):
            self.name = name
            self.frameCount = framecount
            self.texAnim = []
            self.texEnabled = [False] * 8

        def __getitem__(self, i):
            for x in self.texAnim:
                if x.id == i:
                    return x

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
        def unpack(self, bin):
            ''' unpacks the material srt entry '''
            bin.start()
            nameoff, self.enableFlag, uk = bin.read("3I", 12)
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
            bin.store(self.count)   # offsets
            for tex in self.texAnim:
                bin.recall()
                tex.unpack(bin)
            bin.end()

        def pack(self, bin):
            ''' Packs the material srt entry '''
            bin.start()
            bin.storeNameRef(self.name)
            # parse enabled
            i = 0
            count = 0
            for x in self.texEnabled:
                i <<= 1
                if x:
                    i |= 1
                    count +=  1
            bin.write("2I", 8, i, 0)
            bin.mark(count)
            for tex in self.texAnim:
                bin.createRef()
                tex.pack(bin)
            bin.end()
        # -----------------------------------------------------
