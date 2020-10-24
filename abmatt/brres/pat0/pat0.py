"""PAT0 Animations"""
from copy import deepcopy

from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str
from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.node import Node
from abmatt.brres.lib.packing.pack_pat0 import PackPat0
from abmatt.brres.lib.unpacking.unpack_pat0 import UnpackPat0
from abmatt.brres.pat0.pat0_material import Pat0MatAnimation


class Pat0Collection(Node):
    """A collection of pat0 mat animations for a model"""

    def __init__(self, name, parent, pats=None):
        self.collection = []
        if pats:
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
        UnpackPat0(self, binfile)

    def pack(self, binfile):
        PackPat0(self, binfile)