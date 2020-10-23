"""SHP0 """
from copy import deepcopy

from abmatt.brres.lib.binfile import Folder
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str
from abmatt.brres.lib.packing.pack_shp0 import PackShp0
from abmatt.brres.lib.unpacking.unpack_shp0 import UnpackShp0
from abmatt.brres.shp0.shp0_animation import Shp0Animation


class Shp0(SubFile):

    MAGIC = "SHP0"
    EXT = 'shp0'
    VERSION_SECTIONCOUNT = {4: 3, 3: 2}
    EXPECTED_VERSION = 4
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        self.framecount = 1
        self.loop = True
        self.animations = []
        self.strings = []
        super(Shp0, self).__init__(name, parent, binfile)

    def __getitem__(self, item):
        if item == self.SETTINGS[0]:
            return self.framecount
        elif item == self.SETTINGS[1]:
            return self.loop

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.framecount = item.framecount
        self.loop = item.loop
        self.animations = deepcopy(item.animations)
        self.strings = deepcopy(item.strings)

    def unpack(self, binfile):
        UnpackShp0(self, binfile)

    def pack(self, binfile):
        PackShp0(self, binfile)