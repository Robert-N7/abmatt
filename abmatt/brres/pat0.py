"""PAT0 Animations"""
from copy import deepcopy

from brres.subfile import SubFile, set_anim_str, get_anim_str
from brres.lib.binfile import Folder
from brres.lib.matching import validBool, validInt, validFloat, splitKeyVal, fuzzy_strings
from brres.lib.node import Clipable, Node
from brres.lib.autofix import AUTO_FIXER, Bug


class Pat0Collection(Node):
    """A collection of pat0 mat animations for a model"""

    def __init__(self, name, parent, pats=None):
        self.collection = []
        for x in pats:
            self.collection.extend(x.mat_anims)
        super().__init__(name, parent)

    def __getitem__(self, material_name):
        """Gets animation in collection matching material name"""
        for x in self.collection:
            if x.name == material_name:
                return x

    def __iter__(self):
        for x in self.collection:
            yield x

    def get_used_textures(self):
        used = set()
        for anim in self.collection:
            used |= anim.get_used_textures()
        return used

    def add(self, mat_animation):
        self.collection.append(mat_animation)

    def remove(self, animation):
        self.collection.remove(animation)

    def rename(self, name):
        self.name = name

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>(PAT0)' + self.name if indentation_level else '>(PAT0)' + self.name
        print('{}: {} animations'.format(trace, len(self.collection)))
        indentation_level += 1
        for x in self.collection:
            x.info(key, indentation_level)

    def consolidate(self):
        """Combines the pats, returning list of pat0"""
        n = 0
        pats = []  # for storing pat0s
        for x in self.collection:
            added = False
            for pat in pats:
                if pat.add(x):
                    added = True
                    break
            if not added:  # create new one
                postfix = str(len(pats)) if len(pats) > 0 else ''
                s = Pat0(self.name + postfix, self.parent)
                if not s.add(x):
                    print('Error has occurred')
                pats.append(s)
        return pats


class Pat0MatAnimation(Clipable):
    """Single material animation"""

    SETTINGS = ('framecount', 'loop', 'keyframe')
    LOUDNESS = 2
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, parent, framecount=100, loop=True, binfile=None):
        self.enabled = True
        self.fixedTexture = False
        self.hasTexture = True
        self.hasPalette = False
        self.frames = []
        self.framecount = framecount
        self.loop = loop
        self.brres_textures = parent.get_texture_map() if parent else None
        super(Pat0MatAnimation, self).__init__(name, parent, binfile)


    def __deepcopy__(self, memodict={}):
        tex = self.brres_textures
        self.brres_textures = None
        copy = super().__deepcopy__(memodict)
        self.brres_textures = tex
        return copy

    def paste(self, item):
        self.enabled = item.enabled
        self.fixedTexture = item.fixedTexture
        self.hasTexture = item.hasTexture
        self.hasPalette = item.hasPalette
        self.frames = deepcopy(item.frames)
        self.framecount = item.framecount
        self.loop = item.loop

    def create_brres_tex_ref(self, brres_textures):
        self.brres_textures = brres_textures

    def get_used_textures(self):
        return {x.tex for x in self.frames}

    def set_str(self, key, value):
        if key == 'loop':
            self.loop = validBool(value)
        elif key == 'framecount':
            self.framecount = validInt(value, 0, 0x7FFFFFFF)
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

    def updateName(self, new_name):
        self.name = new_name

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
                if not result:
                    b.fix_des = 'Remove ref'
                    if self.REMOVE_UNKNOWN_REFS:
                        mark_for_removal.append(f.tex)
                        b.resolve()
        if mark_for_removal:
            self.frames = [x for x in self.frames if x.tex not in mark_for_removal]

    def check_name(self, name):
        if self.brres_textures and name not in self.brres_textures:
            AUTO_FIXER.warn('No texture found matching frame {}'.format(name), 3)

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

    def info(self, prefix='', key=None, indentation=0):
        prefix = '  ' * indentation + self.name if indentation else '>(PAT0)' + self.name
        if key:
            print('{}: {}'.format(prefix, self.get_str(key)))
        else:
            val = prefix + ': '
            for x in self.SETTINGS:
                val += ' ' + x + ':' + str(self.get_str(x))
            print(val)

    def calcFrameScale(self):
        return 1 / (self.frames[-1].frame_id - self.frames[0].frame_id)

    # ------------------------------------------ PACKING -------------------------------------------------------------
    def unpack_frames(self, binfile):
        # frame header
        size, _, scale_factor = binfile.read('2Hf', 8)
        frames = self.frames
        for i in range(size):
            frame_id, tex_id, plt_id = binfile.read('f2H', 8)
            if frame_id > self.framecount:
                AUTO_FIXER.warn('Unpacked Pat0 {} frame index out of range'.format(self.name), 1)
                break
            frames.append(self.Frame(frame_id, tex_id, plt_id))

    def hook_textures(self, textures):
        m = len(textures)
        for x in self.frames:
            if x.tex >= m:
                x.tex = textures[0]
                AUTO_FIXER.warn('Unpacked Pat0 {} tex_id out of range'.format(self.name), 1)
            else:
                x.tex = textures[x.tex]

    def pack_frames(self, binfile, textures):
        frames = self.frames
        binfile.write('2Hf', len(frames), 0, self.calcFrameScale())
        for x in frames:
            texture_id = textures.index(x.tex)
            binfile.write('f2H', x.frame_id, texture_id, 0)

    def save(self, dest, overwrite):
        # create the pat0
        p = Pat0(self.name, self.parent)
        p.add(self)
        p.save(dest, overwrite)

    def pack(self, binfile):
        offset = binfile.start()
        binfile.storeNameRef(self.name)
        # self.fixedTexture = len(self.frames) <= 1       # todo, check fixed texture formatting/why?
        flags = self.enabled | self.fixedTexture << 1 | self.hasTexture << 2 | self.hasPalette << 3
        binfile.write('I', flags)
        binfile.mark()
        binfile.end()
        return offset

    def unpack_flags(self, binfile):
        binfile.advance(4)  # already have name
        [flags] = binfile.read('I', 4)
        self.enabled = flags & 1
        self.fixedTexture = flags >> 1 & 1
        # if self.fixedTexture:
        #     print('{} Fixed texture!'.format(self.name))
        self.hasTexture = flags >> 2 & 1
        self.hasPalette = flags >> 3 & 1

    def unpack(self, binfile):
        binfile.start()
        self.unpack_flags(binfile)
        [offset] = binfile.read('I', 4)
        binfile.offset = offset + binfile.beginOffset
        self.unpack_frames(binfile)
        binfile.end()
        return self


class Pat0(SubFile):
    """ Pat0 animation class """

    EXT = 'pat0'
    SETTINGS = ('framecount', 'loop')
    MAGIC = "PAT0"
    # Sections:
    #   0: data
    #   1: texture Table
    #   2: palette Table
    #   3: texture ptr Table
    #   4: palette ptr Table
    #   5: user data
    VERSION_SECTIONCOUNT = {3: 5, 4: 6}
    EXPECTED_VERSION = 4

    def __init__(self, name, parent, binfile=None):
        self.n_str = 1
        self.version = 4
        self.mat_anims = []
        super(Pat0, self).__init__(name, parent, binfile)

    def begin(self):
        self.framecount = 100
        self.loop = True

    def add(self, x):
        if not self.mat_anims:
            self.framecount = x.framecount
            self.loop = x.loop
            self.mat_anims.append(x)
            return True
        elif x.framecount == self.framecount and x.loop == self.loop:
            self.mat_anims.append(x)
            return True
        return False

    def getTextures(self):
        textures = []
        for x in self.mat_anims:
            x.getTextures(textures)
        return textures

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.framecount = item.framecount
        self.loop = item.loop
        self.mat_anims = deepcopy(item.mat_anims)


    def unpack(self, binfile):
        self._unpack(binfile)
        origPathOffset, self.framecount, num_mats, num_tex, num_plt, self.loop = binfile.read('I4HI', 24)
        if num_plt:
            raise ValueError('Palettes unsupported! Detected palette while parsing')
        assert origPathOffset == 0
        binfile.recall()  # section 0
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            name = folder.recallEntryI()
            anim = Pat0MatAnimation(name, self.parent.get_texture_map(), self.framecount, self.loop).unpack(binfile)
            self.mat_anims.append(anim)
        binfile.recall()  # section 1
        textures = []
        binfile.start()
        for i in range(num_tex):
            textures.append(binfile.unpack_name())
        binfile.end()
        for x in self.mat_anims:
            x.hook_textures(textures)
        binfile.end()

    def pack(self, binfile):
        textures = self.getTextures()
        anims = self.mat_anims
        self._pack(binfile)
        binfile.write('I4HI', 0, self.framecount, len(anims), len(textures), 0, self.loop)
        binfile.createRef()  # section 0: data
        folder = Folder(binfile)  # index group
        for x in anims:
            folder.addEntry(x.name)
        folder.pack(binfile)
        offsets = []
        for x in anims:  # Headers/flags
            folder.createEntryRefI()
            offsets.append(x.pack(binfile))  # todo, check if the fixed flag changes things
        for x in anims:  # key frame lists
            binfile.createRefFrom(offsets.pop(0))
            x.pack_frames(binfile, textures)

        binfile.createRef()  # section 1: textures
        binfile.start()
        for x in textures:
            binfile.storeNameRef(x)
        binfile.end()
        # skip palettes
        binfile.createRef(3, False)  # section 3: bunch of null
        binfile.advance(len(textures) * 4)
        binfile.end()
