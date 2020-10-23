"""CHR0 Subfile"""
from copy import copy

from abmatt.brres.lib.binfile import Folder
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str
from abmatt.brres.lib.packing.pack_chr0 import PackChr0
from abmatt.brres.lib.unpacking.unpack_chr0 import UnpackChr0


class Chr0(SubFile):
    """ Chr0 class representation """

    MAGIC = "CHR0"
    EXT = 'chr0'
    VERSION_SECTIONCOUNT = {5: 2, 3: 1}
    EXPECTED_VERSION = 5
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        self.animations = []
        super(Chr0, self).__init__(name, parent, binfile)

    def begin(self, initial_values=None):
        self.framecount = 1
        self.loop = True
        self.scaling_rule = 0

    class ModelAnim:
        def __init__(self, name, offset):
            self.name = name
            self.offset = offset  # since we don't parse data... store name offsetg

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.framecount = item.framecount
        self.loop = item.loop
        self.data = copy(item.data)

    def unpack(self, binfile):
        UnpackChr0(self, binfile)

    def pack(self, binfile):
        PackChr0(self, binfile)