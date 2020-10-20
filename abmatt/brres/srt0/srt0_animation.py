from copy import deepcopy, copy

from autofix import Bug
from brres.lib.matching import validFloat, splitKeyVal, validInt, validBool, MATCHING
from brres.lib.node import Clipable


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
        return self.entries == other.entries
        # my_entries = self.entries
        # other_entries = other.entries
        # if len(my_entries) != len(other_entries):
        #     return False
        # for i in range(len(my_entries)):
        #     e = my_entries[i]
        #     o = other_entries[i]
        #     if e.index != o.index or e.value != o.value or e.delta != o.delta:
        #         return False
        # return True

    def __str__(self):
        val = '('
        for x in self.entries:
            val += str(x) + ', '
        return val[:-2] + ')'

    def isDefault(self, is_scale):
        if len(self.entries) > 1:
            return False
        elif len(self.entries) < 1:
            return True
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


class SRTTexAnim(Clipable):
    """ A single texture animation entry in srt0 under material """
    SETTINGS = ('xscale', 'yscale', 'rot', 'xtranslation', 'ytranslation')

    def __init__(self, name, framecount, parent, binfile=None):
        self.animations = {
            'xscale': SRTKeyFrameList(framecount, 1),
            'yscale': SRTKeyFrameList(framecount, 1),
            'rot': SRTKeyFrameList(framecount),
            'xtranslation': SRTKeyFrameList(framecount),
            'ytranslation': SRTKeyFrameList(framecount)
        }
        super(SRTTexAnim, self).__init__(name, parent, binfile)

    def __eq__(self, other):
        return self.animations == other.animations

    # ---------------------- CLIPABLE -------------------------------------------------------------
    def paste(self, item):
        self.animations = deepcopy(item.animations)
        self.mark_modified()

    # -------------------------------------------------------------------------
    # interfacing
    def get_str(self, item):
        return self.animations[item]

    def set_str(self, key, value):
        if value in ('disabled', 'none', 'remove'):
            is_scale = True if 'scale' in key else False
            self.animations[key].clearFrames(is_scale)
        else:
            keyframes = value.strip('()').split(',')
            anim = self.animations[key]
            for x in keyframes:
                key2, value = splitKeyVal(x)
                anim[key2] = value
        self.mark_modified()

    def __deepcopy__(self, memodict={}):
        ret = SRTTexAnim(self.name, self.parent.framecount, None)
        ret.animations = deepcopy(self.animations)
        return ret

    def info(self, key=None, indentation_level=0):
        id = self.name if self.name else str(self.name)
        trace = '  ' * indentation_level + 'Tex:' + id if indentation_level else '>(SRT0)' + self.parent.name + '->Tex:' + id
        if not key:
            for x in self.SETTINGS:
                anim = self.get_str(x)
                if len(anim) > 1:
                    trace += ' ' + x + ':' + str(anim)
            print(trace)
        else:
            print('{}\t{}:{}'.format(trace, key, self.get_str(key)))

    def setKeyFrame(self, animType, value, index=0):
        """ Adds a key frame to the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        val = self.animations[animType].setKeyFrame(value, index)
        self.mark_modified()
        return val

    def removeFrame(self, animType, index):
        """ Removes a key frame from the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        val = self.animations[animType].removeKeyFrame(index)
        self.mark_modified()
        return val

    def clearFrames(self, animType):
        """ clears frames for an animation type
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        is_scale = True if 'scale' in animType else False
        val = self.animations[animType].clearFrames(is_scale)
        self.mark_modified()
        return val

    def setFrameCount(self, frameCount):
        """ Sets the frame count """
        animations = self.animations
        for x in animations:
            animations[x].setFrameCount(frameCount)
        self.mark_modified()


class SRTMatAnim(Clipable):
    """ An entry in the SRT, supports multiple tex refs """

    SETTINGS = ('framecount', 'loop', 'layerenable')
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, frame_count=1, looping=True, parent=None, binfile=None):
        self.parent = parent
        self.framecount = frame_count
        self.tex_animations = []
        self.texEnabled = [False] * 8
        self.loop = looping
        super(SRTMatAnim, self).__init__(name, parent, binfile)

    def __eq__(self, other):
        return self.framecount == other.framecount and self.loop == other.loop \
               and self.texEnabled == other.texEnabled and self.tex_animations == other.tex_animations

    def mark_unmodified(self):
        self.is_modified = False
        self._mark_unmodified_group(self.tex_animations)

    def get_str(self, key):
        if key == 'framecount':
            return self.framecount
        elif key == 'loop':
            return self.loop
        elif key == 'layerenable':
            return self.texEnabled

    def set_str(self, key, value):
        if key == 'framecount':
            i = validInt(value, 1, 0x7FFFFFFF)
            if i != self.framecount:
                self.framecount = i
                for x in self.tex_animations:
                    x.setFrameCount(i)
                self.mark_modified()
        elif key == 'loop':
            loop = validBool(value)
            if self.loop != loop:
                self.loop = loop
                self.mark_modified()
        elif key == 'layerenable':
            key, value = splitKeyVal(value)
            key = validInt(key, 0, 8)
            value = validBool(value)
            if value != self.texIsEnabled(key):
                self.texEnable(key) if value else self.texDisable(key)
                self.mark_modified()

    # ------------------ PASTE ---------------------------
    def paste(self, item):
        self.loop = item.loop
        self.texEnabled = copy(item.texEnabled)
        self.setFrameCount(item.framecount)
        self.tex_animations = [deepcopy(x) for x in item.tex_animations]
        # setup parent
        for x in self.tex_animations:
            x.parent = self
        self.updateLayerNames(self.parent)
        self.mark_modified()

    def setFrameCount(self, count):
        self.framecount = count
        for x in self.tex_animations:
            x.setFrameCount(count)

    def setMaterial(self, material):
        self.parent = material
        self.updateLayerNames(material)

    def texEnable(self, i):
        if not self.texEnabled[i]:
            self.texEnabled[i] = True
            anim = SRTTexAnim(i, self.framecount, self)
            self.tex_animations.append(anim)
            layer = self.parent.getLayerI(i)
            if layer:
                anim.real_name = layer.name
            self.mark_modified()

    def texDisable(self, i):
        if self.texEnabled[i]:
            self.texEnabled[i] = False
            for x in self.tex_animations:
                if x.name == i:
                    self.tex_animations.remove(x)
                    self.mark_modified()
                    break

    def texIsEnabled(self, i):
        return self.texEnabled[i]

    def getTexAnimationByName(self, name):
        for x in self.tex_animations:
            if x.real_name == name:
                return x

    def getTexAnimationByID(self, id):
        if not self.texEnabled[id]:
            return None
        for x in self.tex_animations:
            if x.name == id:
                return x

    # ------------------------------- ADD -----------------------------
    def addLayer(self):
        """Adds layer at first available location"""
        for i in range(len(self.texEnabled)):
            if not self.texEnabled[i]:
                self.texEnable(i)
                self.mark_modified()
                return
        raise ValueError('{} Unable to add animation layer, maxed reached'.format(self.name))

    def addLayerByName(self, name):
        """Adds layer if found"""
        i = self.parent.getLayerByName(name)
        if i > 0:
            self.texEnable(i)
            self.mark_modified()
        raise ValueError('{} Unknown layer {}'.format(self.name, name))

    # -------------------------------- Remove -------------------------------------------
    def removeLayer(self):
        """Removes last layer found"""
        for i in range(len(self.texEnabled) - 1, -1, -1):
            if self.texEnabled[i]:
                self.texDisable(i)
                self.mark_modified()
                return
        raise ValueError('{} No layers left to remove'.format(self.name))

    def removeLayerI(self, i):
        # removes the layer i, shifting as necessary (for removing the layer and animation)
        if self.texEnabled[i]:
            self.tex_animations.remove(self.getTexAnimationByID(i))
            for j in range(i + 1, len(self.texEnabled)):
                self.texEnabled[j-1] = self.texEnabled[j]
            self.mark_modified()

    def removeLayerByName(self, name):
        """Removes the layer if found, (for removing only the animation)"""
        j = 0
        matches = MATCHING.findAll(name, self.tex_animations)
        for i in range(len(self.texEnabled)):
            if self.texEnabled[i]:
                if self.tex_animations[j] in matches:
                    self.texEnabled[i] = False
                    self.tex_animations.pop(j)
                    self.mark_modified()
                    return
                j += 1
        raise ValueError('{} No layer matching {}'.format(self.name, name))

    # -------------------------------- Name updates -------------------------------------
    def updateLayerNameI(self, i, name):
        """updates layer i name"""
        tex = self.getTexAnimationByID(i)
        if tex:
            tex.real_name = name

    def updateLayerNames(self, material):
        """Updates the underlying reference names given material"""
        layers = material.layers
        j = 0  # tex indexer
        for i in range(len(layers)):
            if self.texEnabled[i]:
                self.tex_animations[j].real_name = layers[i].name
                j += 1

    def check(self):
        if not self.parent:
            return
        max = len(self.parent.layers)
        enabled = 0
        for i in range(8):
            if self.texEnabled[i]:
                enabled += 1
                if i >= max:
                    b = Bug(1, 3, "{} SRT layer {} doesn't exist".format(self.parent.name, i), 'Remove srt0 layer')
                    if self.REMOVE_UNKNOWN_REFS:
                        self.texDisable(i)
                        b.resolve()
        if not enabled:
            self.parent.remove_srt0()

    def save(self, dest, overwrite):
        from brres.srt0.srt0 import Srt0
        s = Srt0(self.name, self.parent)
        s.add(self)
        s.save(dest, overwrite)

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '(SRT0)' + self.name if indentation_level else '>(SRT0):' + self.name
        if key in self.SETTINGS:
            print('{}\t{}'.format(trace, self.get_str(key)))
        else:
            trace += ' {} frames loop:{}'.format(self.framecount, self.loop)
            print(trace)
            indentation_level += 1
            for x in self.tex_animations:
                x.info(key, indentation_level)

