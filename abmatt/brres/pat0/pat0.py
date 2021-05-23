"""PAT0 Animations"""
from copy import deepcopy

from abmatt.brres.lib.node import Node
from abmatt.brres.lib.packing.pack_pat0 import PackPat0
from abmatt.brres.lib.unpacking.unpack_pat0 import UnpackPat0
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


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

    def __init__(self, name, parent, binfile=None, base_name=None):
        self.n_str = 1
        self.version = 4
        self.base_name = base_name
        self.mat_anims = []
        super(Pat0, self).__init__(name, parent, binfile)

    def begin(self):
        self.framecount = 100
        self.loop = True

    def __eq__(self, other):
        return super().__eq__(other) and self.framecount == other.framecount and self.loop == other.loop \
               and self.mat_anims == other.mat_anims and self.version == other.version

    def __iter__(self):
        return iter(self.mat_anims)

    def __next__(self):
        return next(self.mat_anims)

    def add(self, x):
        if self.base_name != x.get_anim_base_name():
            return False
        if not self.mat_anims:
            self.framecount = x.framecount
            self.loop = x.loop
            self.mat_anims.append(x)
            return True
        elif x.framecount != self.framecount or x.loop != self.loop:
            return False
        elif x not in self.mat_anims:
            self.mat_anims.append(x)
        return True

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