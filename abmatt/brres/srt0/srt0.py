#!/usr/bin/python
""" Srt0 Brres subfile """

from abmatt.lib.node import Clipable
# ---------------------------------------------------------
from abmatt.brres.lib.packing.pack_srt0 import PackSrt0
from abmatt.brres.lib.unpacking.unpack_srt0 import UnpackSrt0
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


class Srt0(SubFile):
    """ Srt0 Animation """
    SETTINGS = ('framecount', 'loop')
    MAGIC = "SRT0"
    EXT = 'srt0'
    VERSION_SECTIONCOUNT = {4: 1, 5: 2}
    EXPECTED_VERSION = 5

    def __init__(self, name, parent, binfile=None, base_name=None):
        self.matAnimations = []
        self.base_name = base_name
        super(Srt0, self).__init__(name, parent, binfile)

    def begin(self):
        self.framecount = 200
        self.loop = True
        self.matrixmode = 0

    def __iter__(self):
        return iter(self.matAnimations)

    def __next__(self):
        return next(self.matAnimations)

    def set_str(self, key, value):
        set_anim_str(self, key, value)
        for x in self.matAnimations:
            x.set_str(key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.setFrameCount(item.framecount)
        self.setLooping(item.loop)
        Clipable.paste_group(self.matAnimations, item.matAnimations)

    # ---------------------------------------------------------------------
    # interfacing
    def getMatByName(self, matname):
        """ Gets the material animation by material name """
        for x in self.matAnimations:
            if x.name == matname:
                return x

    def setFrameCount(self, count):
        if count >= 1:
            self.framecount = count
            for x in self.matAnimations:
                x.set_frame_count(count)
        else:
            raise ValueError("Frame count {} is not valid".format(count))

    def add(self, mat_animation):
        """ Adds a material animation """
        if self.base_name != mat_animation.get_anim_base_name():
            return False
        if not self.matAnimations:
            self.loop = mat_animation.loop
            self.framecount = mat_animation.framecount
        elif self.framecount != mat_animation.framecount or self.loop != mat_animation.loop:
            return False
        if mat_animation not in self.matAnimations:
            self.matAnimations.append(mat_animation)
        return True

    def removeMatAnimation(self, material):
        """ Removes a material animation """
        ma = self.matAnimations
        for i in range(len(ma)):
            if ma[i].name == material.name:
                return ma.pop(i)
        return None

    def setLooping(self, val):
        self.loop = val
        for x in self.matAnimations:
            x.set_str('loop', 'true')

    # ----------------------------------------------------------------------
    #   PACKING
    def unpack(self, binfile):
        UnpackSrt0(self, binfile)

    def pack(self, binfile):
        PackSrt0(self, binfile)