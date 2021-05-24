"""SCN0 Subfile"""
from copy import deepcopy

from abmatt.brres.lib.packing.pack_scn0 import PackScn0
from abmatt.brres.lib.unpacking.unpack_scn0 import UnpackScn0
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


class Scn0KeyFrameList:
    def __init__(self):
        self.frames = []

    def __eq__(self, other):
        return self.frames == other.frames

    class KeyFrame:
        def __init__(self, value=0, index=0, delta=0):
            self.value = value
            self.index = index
            self.delta = delta

        def __eq__(self, other):
            return self.value == other.value and self.index == other.index and self.delta == other.delta

        def unpack(self, binfile):
            self.delta, self.index, self.value = binfile.read('3f', 12)
            return self

        def pack(self, binfile):
            binfile.write('3f', self.delta, self.index, self.value)

    def unpack(self, binfile):
        num_entries, uk = binfile.read('2H', 4)
        for i in range(num_entries):
            self.frames.append(self.KeyFrame().unpack(binfile))
        return self

    def pack(self, binfile):
        binfile.write('2H', len(self.frames), 0)
        for x in self.frames:
            x.pack(binfile)


class Scn0(SubFile):
    MAGIC = "SCN0"
    EXT = 'scn0'
    VERSION_SECTIONCOUNT = {4: 6, 5: 7}
    EXPECTED_VERSION = 5
    SETTINGS = ('framecount', 'loop')
    FOLDERS = ('LightSet(NW4R)', 'AmbLights(NW4R)', 'Lights(NW4R)', 'Fog(NW4R)', 'Cameras(NW4R)')

    def __init__(self, name, parent, binfile=None):
        self.animations = []
        self.lightsets = []
        self.ambient_lights = []
        self.lights = []
        self.fogs = []
        self.cameras = []
        super(Scn0, self).__init__(name, parent, binfile)

    def __eq__(self, other):
        return super().__eq__(other) and self.animations == other.animations and self.lightsets == other.lightsets \
               and self.ambient_lights == other.ambient_lights and self.lights == other.lights \
               and self.fogs == other.fogs and self.cameras == other.cameras

    def begin(self):
        self.framecount = 1
        self.loop = True

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
        self.lightsets = deepcopy(item.lightsets)
        self.ambient_lights = deepcopy(item.ambient_lights)
        self.lights = deepcopy(item.lights)
        self.fogs = deepcopy(item.fogs)
        self.cameras = deepcopy(item.cameras)

    def unpack(self, binfile):
        UnpackScn0(self, binfile)

    def pack(self, binfile):
        PackScn0(self, binfile)