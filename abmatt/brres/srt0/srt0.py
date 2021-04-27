#!/usr/bin/python
""" Srt0 Brres subfile """

from abmatt.brres.lib.node import Clipable, Node
# ---------------------------------------------------------
from abmatt.brres.lib.packing.pack_srt0 import PackSrt0
from abmatt.brres.lib.unpacking.unpack_srt0 import UnpackSrt0
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


class SRTCollection(Node):
    """A collection of srt mat animations for a model"""

    def __init__(self, name, parent, srts=None):
        self.collection = []
        if srts:
            for x in srts:
                self.collection.extend(x.matAnimations)
        super().__init__(name, parent)

    def __getitem__(self, material_name):
        """Gets animation in collection matching material name"""
        for x in self.collection:
            if x.name == material_name:
                return x

    def __len__(self):
        return len(self.collection)

    def __iter__(self):
        for x in self.collection:
            yield x

    def add(self, mat_animation):
        self.collection.append(mat_animation)

    def remove(self, animation):
        self.collection.remove(animation)

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + '>(SRT0)' + self.name if indentation_level else '>(SRT0)' + self.name
        print('{}: {} animations'.format(trace, len(self.collection)))
        indentation_level += 1
        for x in self.collection:
            x.info(key, indentation_level)

    def consolidate(self):
        """Combines the srts, returning list of SRT0"""
        n = 0
        srts = []  # for storing srt0s
        for x in self.collection:
            added = False
            for srt in srts:
                if srt.add(x):
                    added = True
                    break
            if not added:  # create new one
                postfix = str(len(srts) + 1) if len(srts) > 0 else ''
                s = Srt0(self.name + postfix, self.parent)
                if not s.add(x):
                    print('Error has occurred')
                srts.append(s)
        return srts


class Srt0(SubFile):
    """ Srt0 Animation """
    SETTINGS = ('framecount', 'loop')
    MAGIC = "SRT0"
    EXT = 'srt0'
    VERSION_SECTIONCOUNT = {4: 1, 5: 2}
    EXPECTED_VERSION = 5

    def __init__(self, name, parent, binfile=None):
        self.matAnimations = []
        super(Srt0, self).__init__(name, parent, binfile)

    def begin(self):
        self.framecount = 200
        self.loop = True
        self.matrixmode = 0


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
                x.setFrameCount(count)
        else:
            raise ValueError("Frame count {} is not valid".format(count))

    def add(self, mat_animation):
        """ Adds a material animation """
        if not self.matAnimations:
            self.loop = mat_animation.loop
            self.framecount = mat_animation.framecount
        elif self.framecount != mat_animation.framecount or self.loop != mat_animation.loop:
            return False
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