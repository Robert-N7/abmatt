import string
from copy import deepcopy, copy

from abmatt.autofix import Bug, AutoFix
from abmatt.brres.key_frame_list import KeyFrameList
from abmatt.brres.lib.matching import splitKeyVal, validInt, validBool, MATCHING, parseValStr
from abmatt.brres.lib.node import Clipable


class SRTTexAnim(Clipable):
    """ A single texture animation entry in srt0 under material """
    SETTINGS = ('xscale', 'yscale', 'rot', 'xtranslation', 'ytranslation')

    def __init__(self, name, framecount, parent, binfile=None):
        self.animations = {
            'xscale': KeyFrameList(framecount, 1),
            'yscale': KeyFrameList(framecount, 1),
            'rot': KeyFrameList(framecount),
            'xtranslation': KeyFrameList(framecount),
            'ytranslation': KeyFrameList(framecount)
        }
        super(SRTTexAnim, self).__init__(name, parent, binfile)

    def __eq__(self, other):
        return super().__eq__(other) and self.animations == other.animations

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
            self.animations[key].clear_frames(is_scale)
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
        id = str(self.name)
        trace = '>' + '  ' * indentation_level + 'Tex:' + id if indentation_level else '>(SRT0)' \
                                                                                 + self.parent.name + '->Tex:' + id
        if not key:
            for x in self.SETTINGS:
                anim = self.get_str(x)
                if len(anim) > 1:
                    trace += ' ' + x + ':' + str(anim)
            AutoFix.info(trace, 1)
        else:
            AutoFix.info('{}\t{}:{}'.format(trace, key, self.get_str(key)), 1)

    def set_key_frame(self, animType, value, index=0):
        """ Adds a key frame to the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        val = self.animations[animType].set_key_frame(value, index)
        self.mark_modified()
        return val

    def remove_frame(self, animType, index):
        """ Removes a key frame from the animation
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        val = self.animations[animType].remove_key_frame(index)
        self.mark_modified()
        return val

    def clear_frames(self, animType):
        """ clears frames for an animation type
            animType: xscale|yscale|rotation|xtranslation|ytranslation
        """
        is_scale = True if 'scale' in animType else False
        val = self.animations[animType].clear_frames(is_scale)
        self.mark_modified()
        return val

    def set_frame_count(self, frameCount):
        """ Sets the frame count """
        animations = self.animations
        for x in animations:
            animations[x].set_frame_count(frameCount)
        self.mark_modified()


class SRTMatAnim(Clipable):
    """ An entry in the SRT, supports multiple tex refs """

    SETTINGS = ('framecount', 'loop', 'layerenable')
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, frame_count=1, looping=True, parent=None, binfile=None):
        self.parent = parent
        self.framecount = frame_count
        self.parent_base_name = parent.get_anim_base_name() if parent else None
        self.tex_animations = []
        self.texEnabled = [False] * 8
        self.materials = []
        self.loop = looping
        super(SRTMatAnim, self).__init__(name, parent, binfile)

    def __deepcopy__(self, memodict=None):
        copy = SRTMatAnim(self.name, self.framecount, self.loop)
        copy.parent_base_name = self.parent_base_name
        copy.texEnabled = [x for x in self.texEnabled]
        copy.tex_animations = deepcopy(self.tex_animations)
        return copy

    def __eq__(self, other):
        return super().__eq__(other) \
               and self.framecount == other.framecount and self.loop == other.loop \
               and self.texEnabled == other.texEnabled and self.tex_animations == other.tex_animations

    def __mat_with_max_layers(self):
        v = [len(x.layers) for x in self.materials]
        return self.materials[v.index(max(v))]

    def get_anim_base_name(self):
        if not self.parent_base_name:
            if self.parent:
                self.parent_base_name = self.parent.get_anim_base_name()
            elif self.materials:
                self.parent_base_name = self.materials[0].get_anim_base_name()
        return self.parent_base_name

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
                    x.set_frame_count(i)
                self.mark_modified()
        elif key == 'loop':
            loop = validBool(value)
            if self.loop != loop:
                self.loop = loop
                self.mark_modified()
        elif key == 'layerenable':
            if value.startswith('[') or value.startswith('('):  # list/iterable
                items = parseValStr(value)
                for i in range(len(items)):
                    val = validBool(items[i])
                    if val:
                        self.tex_enable(i)
                    else:
                        self.tex_disable(i)
            else:
                key, value = splitKeyVal(value)
                key = validInt(key, 0, 8)
                value = validBool(value)
                if value != self.tex_is_enabled(key):
                    self.tex_enable(key) if value else self.tex_disable(key)
                    self.mark_modified()

    # ------------------ PASTE ---------------------------
    def paste(self, item):
        self.loop = item.loop
        self.texEnabled = copy(item.texEnabled)
        self.set_frame_count(item.framecount)
        self.tex_animations = [deepcopy(x) for x in item.tex_animations]
        # setup parent
        for x in self.tex_animations:
            x.parent = self
        self.update_layer_names()
        self.mark_modified()

    def set_frame_count(self, count):
        self.framecount = count
        for x in self.tex_animations:
            x.set_frame_count(count)

    def set_material(self, material):
        self.materials.append(material)
        self.update_layer_names()

    def remove_material(self, material):
        if material in self.materials:
            self.materials.remove(material)

    def tex_enable(self, i):
        if not self.texEnabled[i]:
            self.texEnabled[i] = True
            anim = SRTTexAnim(i, self.framecount, self)
            self.tex_animations.append(anim)
            layer = self.__mat_with_max_layers().getLayerI(i)
            if layer:
                anim.real_name = layer.name
            self.mark_modified()

    def tex_disable(self, i):
        if self.texEnabled[i]:
            self.texEnabled[i] = False
            for x in self.tex_animations:
                if x.name == i:
                    self.tex_animations.remove(x)
                    self.mark_modified()
                    break

    def tex_is_enabled(self, i):
        return self.texEnabled[i]

    def get_tex_animation_by_name(self, name):
        for x in self.tex_animations:
            if x.real_name == name:
                return x

    def get_tex_animation_by_id(self, id):
        if not self.texEnabled[id]:
            return None
        for x in self.tex_animations:
            if x.name == id:
                return x

    # ------------------------------- ADD -----------------------------
    def add_layer(self):
        """Adds layer at first available location"""
        for i in range(len(self.texEnabled)):
            if not self.texEnabled[i]:
                self.tex_enable(i)
                self.mark_modified()
                return
        raise ValueError('{} Unable to add animation layer, maxed reached'.format(self.name))

    def add_layer_by_name(self, name):
        """Adds layer if found"""
        for x in self.materials:
            i = x.getLayerByName(name)
            if i:
                self.tex_enable(i)
                self.mark_modified()
                return
        raise ValueError('{} Unknown layer {}'.format(self.name, name))

    # -------------------------------- Remove -------------------------------------------
    def remove_layer(self):
        """Removes last layer found"""
        for i in range(len(self.texEnabled) - 1, -1, -1):
            if self.texEnabled[i]:
                self.tex_disable(i)
                self.mark_modified()
                return
        raise ValueError('{} No layers left to remove'.format(self.name))

    def remove_layer_i(self, i):
        # removes the layer i, shifting as necessary (for removing the layer and animation)
        if self.texEnabled[i]:
            self.tex_animations.remove(self.get_tex_animation_by_id(i))
            for j in range(i + 1, len(self.texEnabled)):
                self.texEnabled[j-1] = self.texEnabled[j]
            self.mark_modified()

    def remove_layer_by_name(self, name):
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
    def update_layer_name_i(self, i, name):
        """updates layer i name"""
        tex = self.get_tex_animation_by_id(i)
        if tex:
            tex.real_name = name

    def update_layer_names(self):
        """Updates the underlying reference names given material"""
        for material in self.materials:
            layers = material.layers
            j = 0  # tex indexer
            for i in range(len(layers)):
                if self.texEnabled[i]:
                    self.tex_animations[j].real_name = layers[i].name
                    j += 1
            return

    def check(self):
        if not self.materials:
            return
        maximum = max(len(x.layers) for x in self.materials)
        enabled = 0
        for i in range(8):
            if self.texEnabled[i]:
                enabled += 1
                if i >= maximum:
                    b = Bug(1, 3, "{} SRT layer {} doesn't exist".format(self.name, i), 'Remove srt0 layer')
                    if self.REMOVE_UNKNOWN_REFS:
                        self.tex_disable(i)
                        b.resolve()
        if not enabled:
            mats = self.materials
            self.materials = []
            for x in mats:
                x.remove_srt0()

    def save(self, dest, overwrite):
        from abmatt.brres.srt0.srt0 import Srt0
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

