#!/usr/bin/python
""" Srt0 Brres subfile """
from copy import deepcopy, copy

from abmatt.binfile import Folder, printCollectionHex
from abmatt.matching import validInt, validBool, validFloat, splitKeyVal, matches, Clipable
from abmatt.subfile import SubFile
from abmatt.autofix import AUTO_FIXER, Bug


# ---------------------------------------------------------
class SRTCollection:
    """A collection of srt mat animations for a model"""

    def __init__(self, name, parent, srts=None):
        self.collection = []
        self.name = name  # takes on model name
        self.parent = parent
        if srts:
            for x in srts:
                self.collection.extend(x.matAnimations)

    def __getitem__(self, material_name):
        """Gets animation in collection matching material name"""
        for x in self.collection:
            if x.name == material_name:
                return x

    def __iter__(self):
        for x in self.collection:
            yield x

    def rename(self, new_name):
        self.name = new_name

    def add(self, mat_animation):
        self.collection.append(mat_animation)

    def remove(self, animation):
        self.collection.remove(animation)

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>(SRT0)' + self.name if indentation_level else '>(SRT0)' + self.name
        print('{}: {} animations'.format(trace, len(self.collection)))
        indentation_level += 1
        for x in self.collection:
            x.info(key, indentation_level)

    def consolidate(self):
        """Combines the srts, returning list of SRT0"""
        n = 0
        srts = []  # for storing srt0s
        for x in self.collection:
            added = False
            for srt in srts:
                if srt.add(x):
                    added = True
                    break
            if not added:  # create new one
                postfix = str(len(srts) + 1) if len(srts) > 0 else ''
                s = Srt0(self.name + postfix, self.parent, x.framecount, x.looping)
                if not s.add(x):
                    print('Error has occurred')
                srts.append(s)
        return srts


class SRTKeyFrameList:
    """ Representing an srt non-fixed animation list
        could be scale/rotation/translation
        Always has 1 entry at index 0
    """

    class SRTKeyFrame:
        """ A single animation entry """

        def __init__(self, value, index=0, delta=0):
            self.index = float(index)  # frame index
            self.value = float(value)  # value
            self.delta = float(delta)  # change per frame

        def __eq__(self, other):
            return self.index == other.index and self.value == other.value and self.delta == other.delta

        def __str__(self):
            return '({}:{}:{})'.format(self.index, self.value, self.delta)

    def __init__(self, frameCount, start_value=0):
        self.framecount = frameCount
        self.entries = [self.SRTKeyFrame(start_value)]

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, key):
        key = validFloat(key, 0, self.framecount + .0001)
        return self.getFrame(key)

    def __setitem__(self, key, value):
        key = validFloat(key, 0, self.framecount + .0001)
        if value in ('disabled', 'none', 'remove'):
            self.removeKeyFrame(key)
        else:
            delta = None
            if ':' in value:
                value, delta = splitKeyVal(value)
                delta = validFloat(value, -0x7FFFFFFF, 0x7FFFFFFF)
            value = validFloat(value, -0x7FFFFFFF, 0x7FFFFFFF)
            self.setKeyFrame(value, key, delta)

    def __eq__(self, other):
        my_entries = self.entries
        other_entries = other.entries
        if len(my_entries) != len(other_entries):
            return False
        for i in range(len(my_entries)):
            e = my_entries[i]
            o = other_entries[i]
            if e.index != o.index or e.value != o.value or e.delta != o.delta:
                return False
        return True

    def __str__(self):
        val = '('
        for x in self.entries:
            val += str(x) + ', '
        return val[:-2] + ')'

    def isDefault(self, is_scale):
        if len(self.entries) > 1:
            return False
        return self.entries[0].value == 1 if is_scale else self.entries[0].value == 0

    def isFixed(self):
        return len(self.entries) == 1  # what about delta?

    def setFixed(self, value):
        self.entries = [self.SRTKeyFrame(value)]

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
        if id2 == id1:  # divide by 0
            return self.entries[0].delta
        return (val2 - val1) / (id2 - id1)

    def updateEntry(self, entry_index):
        """Calculates the deltas due to a changed entry"""
        entry = self.entries[entry_index]
        if len(self.entries) < 2:  # one or 0
            entry.delta = 0
        else:
            try:
                next = self.entries[entry_index + 1]
                next_id = next.index
            except IndexError:
                next = self.entries[0]
                next_id = next.index + self.framecount
            prev = self.entries[entry_index - 1]
            if entry_index == 0:
                prev_id = prev.index - self.framecount
            else:
                prev_id = prev.index
            entry.delta = self.calcDelta(entry.index, entry.value, next_id, next.value)
            prev.delta = self.calcDelta(prev_id, prev.value, entry.index, entry.value)

    # ------------------------------------------------ Key Frames ---------------------------------------------
    def setKeyFrame(self, value, index=0, delta=None):
        """ Adds/sets key frame, overwriting any existing frame at index
            automatically updates delta.
        """
        if not 0 <= index <= self.framecount:
            raise ValueError("Frame Index {} out of range.".format(index))
        entries = self.entries
        entry_index = -1
        cntry = None
        for i in range(len(entries)):
            cntry = entries[i]
            if index < cntry.index:  # insert
                cntry = self.SRTKeyFrame(value, index)
                entries.insert(i, cntry)
                entry_index = i
                break
            elif index == cntry.index:  # replace
                cntry.value = value
                new_entry = cntry
                self.updateEntry(i)
                entry_index = i
                break
        if entry_index < 0:  # append it
            cntry = self.SRTKeyFrame(value, index)
            entries.append(cntry)
            self.updateEntry(entry_index)
        if delta is None:
            self.updateEntry(entry_index)
        else:
            cntry.delta = delta

    def removeKeyFrame(self, index):
        """ Removes key frame from list, updating delta """
        if index == 0:
            return
        entries = self.entries
        for i in range(1, len(entries)):
            if entries[i].index == index:
                prev = entries[i - 1]
                if i == len(entries) - 1:  # last entry?
                    next_entry = entries[0]
                    next_id = self.framecount
                else:
                    next_entry = entries[i + 1]
                    next_id = next_entry.index
                prev.value = self.calcDelta(prev.index, prev.value, next_id, next_entry.value)
                entries.pop(i)
                break

    def clearFrames(self, is_scale):
        """ Clears all frames, resetting to one default """
        start_val = 1 if is_scale else 0
        self.entries = [self.SRTKeyFrame(start_val)]

    def setFrameCount(self, frameCount):
        """ Sets frame count, removing extra frames """
        e = self.entries
        self.framecount = frameCount
        for i in range(len(e)):
            if e[i].index > frameCount:
                self.entries = e[:i]  # possibly fix ending delta todo?
                return i
        return 0

    #   ------------------------------------------- PACKING --------------------------------------------------
    def unpack(self, binfile):
        """ unpacks an animation entry list """
        self.entries = []
        # header
        size, uk, fs = binfile.read("2Hf", 8)
        # print('FrameScale: {} i v d'.format(fs))
        # str = ''
        # assert size
        for i in range(size):
            index, value, delta = binfile.read("3f", 12)
            # str += '({},{},{}), '.format(index, value, delta)
            self.entries.append(self.SRTKeyFrame(value, index, delta))
        # print(str[:-2])
        return self

    def pack(self, binfile, framescale):
        """ packs an animation entry list """
        binfile.write("2Hf", len(self.entries), 0, framescale)
        for x in self.entries:
            binfile.write("3f", x.index, x.value, x.delta)


class SRTTexAnim():
    """ A single texture animation entry in srt0 under material """
    SETTINGS = ('xscale', 'yscale', 'rot', 'xtranslation', 'ytranslation')

    def __init__(self, id, framecount, parent):
        self.id = id
        self.name = None
        self.parent = parent
        self.scaleDefault = True  # scale = 1
        self.rotationDefault = True  # rotation = zero
        self.translationDefault = True  # translation = zero
        self.scaleIsotropic = True  # xscale == yscale
        self.xScaleFixed = True
        self.yScaleFixed = True
        self.rotationFixed = True
        self.xTranslationFixed = True
        self.yTranslationFixed = True
        self.animations = {
            'xscale': SRTKeyFrameList(framecount, 1),
            'yscale': SRTKeyFrameList(framecount, 1),
            'rot': SRTKeyFrameList(framecount),
            'xtranslation': SRTKeyFrameList(framecount),
            'ytranslation': SRTKeyFrameList(framecount)
        }

    # -------------------------------------------------------------------------
    # interfacing
    def __getitem__(self, item):
        return self.animations[item]

    def __setitem__(self, key, value):
        if value in ('disabled', 'none', 'remove'):
            is_scale = True if 'scale' in key else False
            self.animations[key].clearFrames(is_scale)
        else:
            keyframes = value.strip('()').split(',')
            anim = self.animations[key]
            for x in keyframes:
                key2, value = splitKeyVal(x)
                anim[key2] = value

    def __deepcopy__(self, memodict={}):
        ret = SRTTexAnim(self.id, self.parent.framecount, None)
        ret.animations = deepcopy(self.animations)
        return ret

    def info(self, key=None, indentation_level=0):
        id = self.name if self.name else str(self.id)
        trace = '  ' * indentation_level + 'Tex:' + id if indentation_level else '>(SRT0)' + self.parent.name + '->Tex:' + id
        if not key:
            for x in self.SETTINGS:
                trace += ' ' + x + ':' + str(self[x])
            print(trace)
        else:
            print('{}\t{}:{}'.format(trace, key, self[key]))

    def setKeyFrame(self, animType, value, index=0):
        """ Adds a key frame to the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        return self.animations[animType].setKeyFrame(value, index)

    def removeFrame(self, animType, index):
        """ Removes a key frame from the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        return self.animations[animType].removeKeyFrame(index)

    def clearFrames(self, animType):
        """ clears frames for an animation type
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        return self.animations[animType].clearFrames()

    def setFrameCount(self, frameCount):
        """ Sets the frame count """
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
        x = self.animations['xscale']  # XScale
        y = self.animations['yscale']  # yscale
        self.xScaleFixed = x.isFixed()
        self.yScaleFixed = y.isFixed()
        self.scaleDefault = x.isDefault(True) and y.isDefault(True)
        self.scaleIsotropic = self.scaleDefault or x == y
        # Rotation
        rot = self.animations['rot']
        self.rotationFixed = rot.isFixed()
        self.rotationDefault = rot.isDefault(False)
        # Translation
        x = self.animations['xtranslation']
        y = self.animations['ytranslation']
        self.xTranslationFixed = x.isFixed()
        self.yTranslationFixed = y.isFixed()
        self.translationDefault = x.isDefault(False) and y.isDefault(False)
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
                self.animations['xscale'].setFixed(val)
                self.animations['yscale'].setFixed(val)
            else:
                offset = binfile.offset
                keyframelist = binfile.bl_unpack(self.animations['xscale'].unpack, False)
                self.animations['yscale'] = deepcopy(keyframelist)
        else:  # not isotropic
            if self.xScaleFixed:
                [val] = binfile.read("f", 4)
                self.animations['xscale'].setFixed(val)
            else:
                binfile.bl_unpack(self.animations['xscale'].unpack, False)
            if self.yScaleFixed:
                [val] = binfile.read("f", 4)
                self.animations['yscale'].setFixed(val)
            else:
                binfile.bl_unpack(self.animations['yscale'].unpack, False)

    def unpackTranslation(self, binfile):
        """ unpacks translation data """
        if self.translationDefault:
            return
        if self.xTranslationFixed:
            [val] = binfile.read("f", 4)
            self.animations['xtranslation'].setFixed(val)
        else:
            binfile.bl_unpack(self.animations['xtranslation'].unpack, False)
        if self.yTranslationFixed:
            [val] = binfile.read("f", 4)
            self.animations['ytranslation'].setFixed(val)
        else:
            binfile.bl_unpack(self.animations['ytranslation'].unpack, False)

    def unpackRotation(self, binfile):
        """ unpacks rotation """
        if not self.rotationDefault:
            if self.rotationFixed:
                [val] = binfile.read("f", 4)
                self.animations['rot'].setFixed(val)
            else:
                binfile.bl_unpack(self.animations['rot'].unpack, False)

    def unpack(self, binfile):
        """ unpacks SRT Texture animation data """
        # m = binfile.read('200B', 0)
        # printCollectionHex(m)
        [code] = binfile.read("I", 4)
        # print('(SRT0){}->{} code:{}'.format(self.parent.name, self.id, code))
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
                binfile.write("f", self.animations['xscale'].getValue())
            else:
                binfile.mark()  # mark to be stored
                has_x_list_offset = True
            if not self.scaleIsotropic:
                if self.yScaleFixed:
                    binfile.write("f", self.animations['yscale'].getValue())
                else:
                    binfile.mark()
                    has_y_list_offset = True
        return [has_x_list_offset, has_y_list_offset]

    def packRotation(self, binfile):
        """ packs rotation data """
        if not self.rotationDefault:
            if self.rotationFixed:
                binfile.write("f", self.animations['rot'].getValue())
            else:
                binfile.mark()
                return True
        return False

    def packTranslation(self, binfile):
        """ packs translation data, returning tuple (hasXTransOffset, hasYTransOffset) """
        hasXTransOffset = hasYTransOffset = False
        if not self.translationDefault:
            if self.xTranslationFixed:
                binfile.write("f", self.animations['xtranslation'].getValue())
            else:
                binfile.mark()
                hasXTransOffset = True
            if self.yTranslationFixed:
                binfile.write("f", self.animations['ytranslation'].getValue())
            else:
                binfile.mark()
                hasYTransOffset = True
        return [hasXTransOffset, hasYTransOffset]

    def packHead(self, binfile):
        """ packs the texture animation entry,
            returns offset markers to be passed to pack data
            (after packing all headers for material)
        """
        code = self.calculateCode()
        # code = self.flagsToInt()
        binfile.write("I", code)
        have_offsets = self.packScale(binfile)
        have_offsets.append(self.packRotation(binfile))
        have_offsets.extend(self.packTranslation(binfile))
        return have_offsets


class SRTMatAnim(Clipable):
    """ An entry in the SRT, supports multiple tex refs """

    SETTINGS = ('framecount', 'loop', 'layerenable')

    def __init__(self, name, frame_count=1, looping=True, material=None):
        self.name = name
        self.material = material  # to be filled
        self.framecount = frame_count
        self.tex_animations = []
        self.texEnabled = [False] * 8
        self.looping = looping

    def __getitem__(self, key):
        if key == 'framecount':
            return self.framecount
        elif key == 'loop':
            return self.looping
        elif key == 'layerenable':
            return self.texEnabled

    def __setitem__(self, key, value):
        if key == 'framecount':
            i = validInt(value, 1, 0x7FFFFFFF)
            self.framecount = i
            for x in self.tex_animations:
                x.setFrameCount(i)
        elif key == 'loop':
            self.looping = validBool(value)
        elif key == 'layerenable':
            key, value = splitKeyVal(value)
            key = validInt(key, 0, 8)
            value = validBool(value)
            self.texEnable(key) if value else self.texDisable(key)

    def rename(self, name):
        self.name = name

    # ------------------ PASTE ---------------------------
    def paste(self, item):
        self.looping = item.looping
        self.texEnabled = copy(item.texEnabled)
        self.setFrameCount(item.framecount)
        self.tex_animations = [deepcopy(x) for x in item.tex_animations]
        # setup parent
        for x in self.tex_animations:
            x.parent = self

    def setFrameCount(self, count):
        self.framecount = count
        for x in self.tex_animations:
            x.setFrameCount(count)

    def setMaterial(self, material):
        self.material = material
        self.updateLayerNames(material)

    def texEnable(self, i):
        if not self.texEnabled[i]:
            self.texEnabled[i] = True
            anim = SRTTexAnim(i, self.framecount, self)
            self.tex_animations.append(anim)
            layer = self.material.getLayerI(i)
            if layer:
                anim.name = layer.name

    def texDisable(self, i):
        if self.texEnabled[i]:
            self.texEnabled[i] = False
            for x in self.tex_animations:
                if x.id == i:
                    self.tex_animations.remove(x)
                    break

    def texIsEnabled(self, i):
        return self.texEnabled[i]

    def getTexAnimationByName(self, name):
        for x in self.tex_animations:
            if x.name == name:
                return x

    def getTexAnimationByID(self, id):
        if not self.texEnabled[id]:
            return None
        j = 0  # indexing tex anims (enabled)
        for i in range(len(self.texEnabled)):
            if self.texEnabled[i]:
                if i == id:
                    return self.tex_animations[j]
                j += 1

    # ------------------------------- ADD -----------------------------
    def addLayer(self):
        """Adds layer at first available location"""
        for i in range(len(self.texEnabled)):
            if not self.texEnabled[i]:
                return self.texEnable(i)
        raise ValueError('{} Unable to add animation layer, maxed reached'.format(self.name))

    def addLayerByName(self, name):
        """Adds layer if found"""
        i = self.material.find(name)
        if i > 0:
            self.texEnable(i)
        raise ValueError('{} Unknown layer {}'.format(self.name, name))

    # -------------------------------- Remove -------------------------------------------
    def removeLayer(self):
        """Removes last layer found"""
        for i in range(len(self.texEnabled) - 1, -1, -1):
            if self.texEnabled[i]:
                return self.texDisable(i)
        raise ValueError('{} No layers left to remove'.format(self.name))

    def removeLayerByName(self, name):
        """Removes the layer if found"""
        j = 0
        for i in range(len(self.texEnabled)):
            if self.texEnabled[i]:
                if matches(name, self.tex_animations[j].name):
                    self.texEnabled[i] = False
                    self.tex_animations.pop(j)
                    return
                j += 1
        raise ValueError('{} No layer matching {}'.format(self.name, name))

    # -------------------------------- Name updates -------------------------------------
    def updateName(self, name):
        self.name = name

    def updateLayerNameI(self, i, name):
        """updates layer i name"""
        tex = self.getTexAnimationByID(i)
        if tex:
            tex.name = name

    def updateLayerNames(self, material):
        """Updates the underlying reference names given material"""
        layers = material.layers
        j = 0  # tex indexer
        for i in range(len(layers)):
            if self.texEnabled[i]:
                self.tex_animations[j].name = layers[i].name
                j += 1

    def check(self):
        if not self.material:
            return
        max = len(self.material.layers)
        enabled = 0
        for i in range(8):
            if self.texEnabled[i]:
                enabled += 1
                if i >= max:
                    b = Bug(1, 3, "{} SRT layer {} doesn't exist".format(self.material.name, i), 'Remove srt0 layer')
                    if b.should_fix():
                        self.texDisable(i)
                        b.resolve()
        if not enabled:
            b = Bug(3, 2, '{} no SRT0 layers enabled'.format(self.material.name), 'Remove SRT0')
            if b.should_fix():
                self.material.remove_srt0()
                b.resolve()

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '(SRT0)' + self.name if indentation_level else '>(SRT0):' + self.name
        if key in self.SETTINGS:
            print('{}\t{}'.format(trace, self[key]))
        else:
            for x in self.SETTINGS:
                trace += ' ' + x + ':' + str(self[x])
            print(trace)
            indentation_level += 1
            for x in self.tex_animations:
                x.info(key, indentation_level)

    # -----------------------------------------------------
    #  Packing
    def consolidate(self, binfile, has_key_frames, frame_lists_offsets):
        """consolidates and packs the frame lists based on the animations that have key frames"""
        frame_scale = Srt0.calcFrameScale(self.framecount)
        for j in range(len(self.tex_animations)):  # Each texture
            has_frames = has_key_frames[j]
            tex = self.tex_animations[j]
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
                        test_list.pack(binfile, frame_scale)

    def unpack(self, binfile):
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
                self.texEnabled[i] = True
                self.tex_animations.append(SRTTexAnim(i, self.framecount, self))
                count += 1
            else:
                self.texEnabled[i] = False
            bit <<= 1
        binfile.store(count)  # offsets
        for tex in self.tex_animations:
            binfile.recall()
            tex.unpack(binfile)
        binfile.end()

    def pack(self, binfile):
        """ Packs the material srt entry """
        self.offset = binfile.start()
        binfile.storeNameRef(self.name)
        # parse enabled
        i = count = 0
        bit = 1
        for x in self.texEnabled:
            if x:
                i |= bit
                count += 1
            bit <<= 1
        binfile.write("2I", i, 0)
        binfile.mark(count)
        has_offsets = []
        animations = self.tex_animations
        for tex in animations:
            binfile.createRef()
            has_offsets.append(tex.packHead(binfile))
        # self.consolidate(binfile, offsets)
        binfile.end()
        return has_offsets
    # -----------------------------------------------------


class Srt0(SubFile):
    """ Srt0 Animation """
    MAGIC = "SRT0"
    VERSION_SECTIONCOUNT = {4: 1, 5: 2}
    EXPECTED_VERSION = 5

    def __init__(self, name, parent, frame_count=1, loop=True):
        super(Srt0, self).__init__(name, parent)
        self.matAnimations = []
        self.framecount = frame_count
        self.looping = loop
        self.version = 5
        self.matrixmode = 0

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

    def add(self, mat_animation):
        """ Adds a material animation """
        if self.framecount == mat_animation.framecount and self.looping == mat_animation.looping:
            self.matAnimations.append(mat_animation)
            return True
        return False

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
        return 1.0 / frameCount if frameCount > 1 else 1

    # ----------------------------------------------------------------------
    #   PACKING
    def unpack(self, binfile):
        self._unpack(binfile)
        uk, self.framecount, self.size, self.matrixmode, self.looping = binfile.read("I2H2I", 16)
        # advance to section 0
        binfile.recall()
        folder = Folder(binfile, "srt0root")
        folder.unpack(binfile)
        while True:
            e = folder.openI()
            if not e:
                break
            mat = SRTMatAnim(e, self.framecount)
            mat.unpack(binfile)
            self.matAnimations.append(mat)
        # binfile.recall()  # section 1 (unknown)
        # self.section1 = binfile.readRemaining(self.byte_len)
        binfile.end()

    def pack(self, binfile):
        """ Packs the data for SRT file """
        self._pack(binfile)
        # self._packData(binfile)
        binfile.write("I2H2I", 0, self.framecount, len(self.matAnimations),
                      self.matrixmode, self.looping)
        binfile.createRef()  # create ref to section 0
        # create index group
        folder = Folder(binfile, "srt0root")
        for x in self.matAnimations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        mat_offsets = []
        for x in self.matAnimations:
            folder.createEntryRefI()
            mat_offsets.append(x.pack(binfile))
        # Now for key frames
        key_frame_lists = {}  # map of offsets to frame lists
        for x in self.matAnimations:
            x.consolidate(binfile, mat_offsets.pop(0), key_frame_lists)
        # binfile.createRef()  # section 1 (unknown)
        # binfile.writeRemaining(self.section1)
        binfile.end()
