"""PAT0 Animations"""
import math

from abmatt.subfile import SubFile
from abmatt.binfile import Folder
from abmatt.matching import validBool, validInt, validFloat, splitKeyVal


class Pat0Collection:
    """A collection of pat0 mat animations for a model"""

    def __init__(self, name, parent, pats=None):
        self.collection = []
        self.name = name  # takes on model name
        self.parent = parent
        for x in pats:
            self.collection.extend(x.mat_anims)

    def __getitem__(self, material_name):
        """Gets animation in collection matching material name"""
        for x in self.collection:
            if x.name == material_name:
                return x

    def __iter__(self):
        for x in self.collection:
            yield x

    def add(self, mat_animation):
        self.collection.append(mat_animation)

    def remove(self, animation):
        self.collection.remove(animation)

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
                s = Pat0(self.name + postfix, self.parent, x.framecount, x.loop)
                if not s.add(x):
                    print('Error has occurred')
                pats.append(s)
        return pats


class Pat0MatAnimation:
    """Single material animation"""

    SETTINGS = ('framecount', 'loop', 'keyframe')

    def __init__(self, name, frame_count=2, loop=True):
        self.enabled = True
        self.fixedTexture = False
        self.hasTexture = True
        self.hasPalette = False
        self.frames = []
        self.name = name
        self.material = None     # to be filled in
        self.brres_textures = None  # to be filled
        self.framecount = frame_count
        self.loop = loop

    def create_brres_tex_ref(self, brres_textures):
        self.brres_textures = brres_textures

    def setMaterial(self, material):
        self.material = material

    def __setitem__(self, key, value):
        if key == 'loop':
            self.loop = validBool(value)
        elif key == 'framecount':
            self.framecount = validInt(value, 0, math.inf)
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

    def __getitem__(self, item):
        if item == 'loop':
            return self.loop
        elif item == 'framecount':
            return self.framecount
        elif item == 'keyframe':
            return self.get_frames()
        raise ValueError('Unknown setting {}, possible are {}'.format(item, self.SETTINGS))

    class Frame:
        def __init__(self, frame_id, tex_name, palette_id=0):
            self.frame_id = frame_id
            self.tex_name = tex_name
            self.palette_id = palette_id

        def __str__(self):
            return str(self.frame_id) + ':' + self.tex_name

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

    def check_name(self, name):
        if self.brres_textures:
            for x in self.brres_textures:
                if x.name == name:
                    return True
            print('WARNING: No texture found matching pat0 animation {}'.format(name))
        return not self.brres_textures

    def set_frame(self, key_frame_id, tex_name):
        if not 0 <= key_frame_id <= self.framecount:
            raise ValueError('Key frame id {} not within (0, {})'.format(key_frame_id, self.framecount))
        if tex_name in ('remove', 'disabled'):
            return self.remove_frame(key_frame_id)
        self.check_name(tex_name)
        for i in range(len(self.frames)):
            x = self.frames[i]
            if key_frame_id == x.frame_id:
                x.tex_name = tex_name
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
        for tex in self.frames:
            if tex.tex_name not in tex_list:
                tex_list.append(tex.tex_name)
        return tex_list

    def info(self, key=None, indentation=0):
        prefix = '  ' * indentation + self.name if indentation else '>(PAT0)' + self.name
        if key:
            print('{}: {}'.format(prefix, self[key]))
        else:
            val = prefix + ': '
            for x in self.SETTINGS:
                val += ' ' + x + ':' + str(self[x])
            print(val)

    def calcFrameScale(self):
        return 1 / (self.frames[-1].frame_id - self.frames[0].frame_id)

    # ------------------------------------------ PACKING -------------------------------------------------------------
    def unpack_frames(self, binfile, textures):
        # frame header
        size, _, scale_factor = binfile.read('2Hf', 8)
        frames = self.frames
        for i in range(size):
            frame_id, tex_id, plt_id = binfile.read('f2H', 8)
            frames.append(self.Frame(frame_id, textures[tex_id], plt_id))

    def pack_frames(self, binfile, textures):
        frames = self.frames
        binfile.write('2Hf', len(frames), 0, self.calcFrameScale())
        for x in frames:
            texture_id = textures.index(x.tex_name)
            binfile.write('f2H', x.frame_id, texture_id, x.palette_id)

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
        if self.fixedTexture:
            print('{} Fixed texture!'.format(self.name))
        self.hasTexture = flags >> 2 & 1
        self.hasPalette = flags >> 3 & 1

    def unpack(self, binfile, textures):
        binfile.start()
        self.unpack_flags(binfile)
        [offset] = binfile.read('I', 4)
        binfile.offset = offset + binfile.beginOffset
        self.unpack_frames(binfile, textures)
        binfile.end()
        return self


class Pat0(SubFile):
    """ Pat0 animation class """

    MAGIC = "PAT0"
    # Sections:
    #   0: data
    #   1: texture Table
    #   2: palette Table
    #   3: texture ptr Table
    #   4: palette ptr Table
    #   5: user data
    VERSION_SECTIONCOUNT = {3: 5, 4: 6}

    def __init__(self, name, parent, frame_count=2, loop=True):
        super(Pat0, self).__init__(name, parent)
        self.frame_count = frame_count
        self.loop = loop
        self.num_entries = 1
        self.n_str = 1
        self.version = 4
        self.mat_anims = []
        self.textures = []

    def add(self, x):
        if x.framecount == self.frame_count and x.loop == self.loop:
            self.mat_anims.append(x)
            x.getTextures(self.textures)
            return True
        return False

    def getTextures(self):
        textures = []
        for x in self.mat_anims:
            x.getTextures(textures)
        return textures

    def unpack(self, binfile):
        self._unpack(binfile)
        origPathOffset, self.frame_count, num_mats, num_tex, num_plt, self.loop = binfile.read('I4HI', 24)
        if num_plt:
            raise ValueError('Palettes unsupported! Detected palette while parsing')
        assert origPathOffset == 0
        binfile.recall(1)  # section 1
        textures = []
        binfile.start()
        for i in range(num_tex):
            textures.append(binfile.unpack_name())
        binfile.end()
        binfile.recall()  # section 0
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            name = folder.recallEntryI()
            anim = Pat0MatAnimation(name, self.frame_count, self.loop).unpack(binfile, textures)
            self.mat_anims.append(anim)
            anim.create_brres_tex_ref(self.parent.textures)
        # remaining = binfile.readRemaining(self.byte_len)
        # printCollectionHex(remaining)
        # ignore the rest
        # binfile.recall()    # section 2: palette
        # binfile.recall()    # section 3: texture ptr table
        # binfile.recall()    # section 4: palette ptr table
        # binfile.recall()    # section 5: user data
        binfile.end()

    def pack(self, binfile):
        textures = self.getTextures()
        anims = self.mat_anims
        self._pack(binfile)
        binfile.write('I4HI', 0, self.frame_count, len(anims), len(textures), 0, self.loop)
        binfile.createRef(0, False)  # section 0: data
        folder = Folder(binfile)    # index group
        for x in anims:
            folder.addEntry(x.name)
        folder.pack(binfile)
        offsets = []
        for x in anims:    # Headers/flags
            folder.createEntryRefI()
            offsets.append(x.pack(binfile))      # todo, check if the fixed flag changes things
        for x in anims:    # key frame lists
            binfile.createRefFrom(offsets.pop(0))
            x.pack_frames(binfile, textures)

        binfile.createRef(1, False)  # section 1: textures
        binfile.start()
        for x in textures:
            binfile.storeNameRef(x)
        binfile.end()
        # skip palettes
        binfile.createRef(3, False)  # section 3: bunch of null
        binfile.advance(len(textures) * 4)
        # skip palettes/userdata
        # binfile.align()
        binfile.end()