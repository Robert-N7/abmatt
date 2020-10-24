"""CLR0 BRRES SUBFILE"""
from copy import deepcopy

from abmatt.brres.subfile import SubFile, get_anim_str, set_anim_str
from abmatt.brres.lib.packing.pack_clr0 import PackClr0
from abmatt.brres.lib.unpacking.unpack_clr0 import UnpackClr0


class Clr0(SubFile):
    """ Clr0 class """
    MAGIC = "CLR0"
    EXT = 'clr0'
    VERSION_SECTIONCOUNT = {4: 2, 3: 1}
    EXPECTED_VERSION = 4
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        self.animations = []
        super(Clr0, self).__init__(name, parent, binfile)

    def begin(self, initial_values=None):
        self.loop = True
        self.framecount = 1

    def paste(self, item):
        self.animations = deepcopy(item.animations)
        self.loop = item.loop
        self.framecount = item.framecount

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def unpack(self, binfile):
        UnpackClr0(self, binfile)

    def pack(self, binfile):
        PackClr0(self, binfile)
