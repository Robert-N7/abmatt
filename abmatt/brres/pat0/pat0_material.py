import string
from copy import deepcopy

from abmatt.autofix import Bug, AutoFix
from abmatt.brres.lib.matching import validBool, validInt, splitKeyVal, validFloat, fuzzy_strings
from abmatt.brres.lib.node import Clipable


class Pat0MatAnimation(Clipable):
    """Single material animation"""

    SETTINGS = ('framecount', 'loop', 'keyframe')
    LOUDNESS = 2
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, parent, framecount=100, loop=True, binfile=None):
        self.enabled = True
        self.fixed_texture = False
        self.has_texture = True
        self.has_palette = False
        self.frames = []
        self.framecount = framecount
        self.loop = loop
        if parent:
            self.parent_base_name = parent.get_anim_base_name()
            self.brres_textures = parent.get_texture_map()
        else:
            self.brres_textures = None
            self.parent_base_name = None
        super(Pat0MatAnimation, self).__init__(name, parent, binfile)

    def get_anim_base_name(self):
        if not self.parent_base_name:
            if self.parent:
                self.parent_base_name = self.parent.get_anim_base_name()
        return self.parent_base_name

    def __eq__(self, other):
        return super().__eq__(other) \
            and self.enabled == other.enabled and self.framecount == other.framecount \
            and self.loop == other.loop and self.frames == other.frames \
            and self.has_fixed_texture() == other.has_fixed_texture()

    def __deepcopy__(self, memodict={}):
        tex = self.brres_textures
        self.brres_textures = None
        copy = super().__deepcopy__(memodict)
        self.brres_textures = tex
        return copy

    def paste(self, item):
        self.enabled = item.enabled
        self.fixed_texture = item.fixed_texture
        self.has_texture = item.has_texture
        self.has_palette = item.has_palette
        self.frames = deepcopy(item.frames)
        self.framecount = item.framecount
        self.loop = item.loop
        self.mark_modified()

    def create_brres_tex_ref(self, brres_textures):
        self.brres_textures = brres_textures

    def get_used_textures(self):
        return {x.tex for x in self.frames}

    def has_fixed_texture(self):
        return self.fixed_texture or len(self.frames) <= 1

    def set_str(self, key, value):
        if key == 'loop':
            loop = validBool(value)
            if loop != self.loop:
                self.loop = loop
                self.mark_modified()
        elif key == 'framecount':
            framecount = validInt(value, 0, 0x7FFFFFFF)
            if framecount != self.framecount:
                self.framecount = framecount
                self.mark_modified()
        elif key == 'keyframe':
            frame_ids = []
            names = []
            # gather/validate ids and names
            keyframes = value.strip('()').split(',')
            max = self.framecount + .001
            for x in keyframes:
                frame_id, tex_name = splitKeyVal(x)
                frame_ids.append(validFloat(frame_id, 0, max))
                names.append(tex_name)
            for i in range(len(frame_ids)):
                self.set_frame(frame_ids[i], names[i])
            self.mark_modified()

    def get_str(self, item):
        if item == 'loop':
            return self.loop
        elif item == 'framecount':
            return self.framecount
        elif item == 'keyframe':
            return self.get_frames()
        raise ValueError('Unknown setting {}, possible are {}'.format(item, self.SETTINGS))

    class Frame:
        def __init__(self, frame_id, tex, palette_id=0):
            self.frame_id = frame_id
            self.tex = tex
            self.palette_id = palette_id

        def __str__(self):
            return str(self.frame_id) + ':' + self.tex

        def __eq__(self, other):
            return self.frame_id == other.frame_id and self.tex == other.tex and self.palette_id == other.palette_id

    def updateName(self, new_name):
        if new_name != self.name:
            self.name = new_name
            self.mark_modified()

    def set_frame_count(self, val):
        self.framecount = val
        self.frames = [x for x in self.frames if x.frame_id <= val]

    def get_frames(self):
        str_val = '('
        for x in self.frames:
            str_val += str(x) + ', '
        return str_val[:-2] + ')'

    def get_frame(self, key_frame_id):
        for x in self.frames:
            if x.frame_id == key_frame_id:
                return x

    def remove_frame(self, key_frame_id):
        for i in range(len(self.frames)):
            if self.frames[i].frame_id == key_frame_id:
                self.frames.pop(i)
                return True
        return False

    def check(self):
        if not self.brres_textures:
            return
        mark_for_removal = []
        for f in self.frames:
            if f.tex not in self.brres_textures and f.tex not in mark_for_removal:
                result = None
                b = Bug(3, 1, 'No Tex0 matching {} in Pat0'.format(f.tex), 'Rename reference')
                if self.RENAME_UNKNOWN_REFS:
                    # fuzz time
                    result = fuzzy_strings(f.tex, self.brres_textures)
                    if result:
                        b.fix_des = 'Rename to {}'.format(result)
                        f.tex = result
                        b.resolve()
                        self.mark_modified()
                if not result:
                    b.fix_des = 'Remove ref'
                    if self.REMOVE_UNKNOWN_REFS:
                        mark_for_removal.append(f.tex)
                        b.resolve()
        if mark_for_removal:
            self.frames = [x for x in self.frames if x.tex not in mark_for_removal]
            self.mark_modified()

    def check_name(self, name):
        if self.brres_textures and name not in self.brres_textures:
            AutoFix.warn('No texture found matching frame {}'.format(name), 3)

    def set_frame(self, key_frame_id, tex_name):
        if not 0 <= key_frame_id <= self.framecount:
            raise ValueError('Key frame id {} not within (0, {})'.format(key_frame_id, self.framecount))
        if tex_name in ('remove', 'disabled'):
            return self.remove_frame(key_frame_id)
        self.check_name(tex_name)
        for i in range(len(self.frames)):
            x = self.frames[i]
            if key_frame_id == x.frame_id:
                x.tex = tex_name
                return x
            elif key_frame_id < x.frame_id:
                anim = self.Frame(key_frame_id, tex_name, 0)
                self.frames.insert(i, anim)
                return anim
        # not found
        anim = self.Frame(key_frame_id, tex_name, 0)
        self.frames.append(anim)
        return anim

    def getTextures(self, tex_list):
        for frame in self.frames:
            if frame.tex not in tex_list:
                tex_list.append(frame.tex)
        return tex_list

    def info(self, key=None, indentation=0):
        prefix = '>' + '  ' * indentation + self.name if indentation else '>(PAT0)' + self.name
        if key:
            AutoFix.info('{}: {}'.format(prefix, self.get_str(key)), 1)
        else:
            val = prefix + ': '
            for x in self.SETTINGS:
                val += ' ' + x + ':' + str(self.get_str(x))
            AutoFix.info(val, 1)

    def calcFrameScale(self):
        return 1 / (self.frames[-1].frame_id - self.frames[0].frame_id)

    # ------------------------------------------ PACKING ------------------------------------------------------------
    def save(self, dest, overwrite):
        # create the pat0
        from abmatt.brres.pat0.pat0 import Pat0
        p = Pat0(self.name, self.parent)
        p.add(self)
        p.save(dest, overwrite)
