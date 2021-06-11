""" BRRES Subfiles """


# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
import os
import string

from abmatt.autofix import Bug, AutoFix
from abmatt.brres.lib.binfile import BinFile
from abmatt.brres.lib.matching import validInt, validBool
from abmatt.brres.lib.node import Clipable, Packable


def set_anim_str(animation, key, value):
    if key == 'framecount':  # framecount
        val = validInt(value, 1)
        animation.framecount = val
    elif key == 'loop':  # loop
        val = validBool(value)
        animation.loop = val
    else:
        return False
    return True


def get_anim_str(animation, key):
    if key == 'framecount':  # framecount
        return animation.framecount
    elif key == 'loop':  # loop
        return animation.loop


class SubFile(Clipable, Packable):
    """
    Brres Sub file Class
    """
    FORCE_VERSION = True

    # Properties
    @property
    def MAGIC(self):
        raise NotImplementedError()

    @property
    def EXT(self):
        raise NotImplementedError()

    @property
    def VERSION_SECTIONCOUNT(self):
        raise NotImplementedError()


    @property
    def EXPECTED_VERSION(self):
        raise NotImplementedError()

    def __init__(self, name, parent, binfile):
        """ initialize with parent of this file """
        super(SubFile, self).__init__(name, parent, binfile)
        self.version = self.EXPECTED_VERSION
        if binfile:
            self.unpack(binfile)

    def get_num_sections(self):
        return self.VERSION_SECTIONCOUNT[self.version]

    def get_anim_base_name(self):
        if self.parent and self.parent.respect_model_names():
            return self.name
        return self.name.rstrip(string.digits)

    def check(self):
        if self.version != self.EXPECTED_VERSION:
            b = Bug(2, 3, '{} {} unusual version {}'.format(self.MAGIC, self.name, self.version),
                    'set to {}'.format(self.EXPECTED_VERSION))
            if self.FORCE_VERSION:
                self.version = self.EXPECTED_VERSION
                b.resolve()
                self.parent.is_modified = True

    def save(self, dest, overwrite):
        if dest is None:
            dest = self.name
        ext = '.' + self.EXT
        if not dest.endswith(ext):
            dest += ext
        if os.path.exists(dest) and not overwrite and not self.OVERWRITE_MODE:
            AutoFix.error('{} already exists!'.format(dest))
            return
        bin = BinFile(dest, 'w')
        self.pack(bin)
        bin.commitWrite()
        return dest
