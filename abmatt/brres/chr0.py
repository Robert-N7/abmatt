"""CHR0 Subfile"""
from copy import copy

from abmatt.brres.key_frame_list import KeyFrameList
from abmatt.brres.lib.node import Node
from abmatt.brres.lib.packing.pack_chr0 import PackChr0
from abmatt.brres.lib.unpacking.unpack_chr0 import UnpackChr0
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


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

    class BoneAnimation(Node):
        def __init__(self, name, parent, binfile=None, framecount=1, loop=True):
            self.framecount = framecount
            self.loop = loop
            self.x_translation = KeyFrameList(framecount)
            self.y_translation = KeyFrameList(framecount)
            self.z_translation = KeyFrameList(framecount)
            self.x_rotation = KeyFrameList(framecount)
            self.y_rotation = KeyFrameList(framecount)
            self.z_rotation = KeyFrameList(framecount)
            self.x_scale = KeyFrameList(framecount, 1.0)
            self.y_scale = KeyFrameList(framecount, 1.0)
            self.z_scale = KeyFrameList(framecount, 1.0)
            # self.offset = offset  # since we don't parse data... store name offsetg
            super().__init__(name, parent, binfile)

        def __eq__(self, other):
            return super().__eq__(other) and self.framecount == other.framecount and self.loop == other.loop \
                   and self.x_translation == other.x_translation and self.y_translation == other.y_translation \
                   and self.z_translation == other.z_translation and self.x_rotation == other.x_rotation \
                   and self.y_rotation == other.y_rotation and self.z_rotation == other.z_rotation \
                   and self.x_scale == other.x_scale and self.y_scale == other.y_scale and self.z_scale == other.z_scale

    def __iter__(self):
        return iter(self.animations)

    def __next__(self):
        return next(self.animations)

    def __eq__(self, other):
        return super().__eq__(other) and self.framecount == other.framecount and self.loop == other.loop \
               and self.scaling_rule == other.scaling_rule and self.animations == other.animations

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