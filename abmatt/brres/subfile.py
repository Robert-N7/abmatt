""" BRRES Subfiles """


# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
import os

from abmatt.brres.lib.binfile import UnpackingError, BinFile
from abmatt.brres.lib.matching import validInt, validBool
from abmatt.brres.lib.node import Clipable
from abmatt.brres.lib.autofix import Bug, AUTO_FIXER


def set_anim_str(animation, key, value):
    if key == 'framecount':  # framecount
        val = validInt(value, 1)
        animation.framecount = val
    elif key == 'loop':  # loop
        val = validBool(value)
        animation.loop = val


def get_anim_str(animation, key):
    if key == 'framecount':  # framecount
        return animation.framecount
    elif key == 'loop':  # loop
        return animation.loop


class SubFile(Clipable):
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

    def _unpackData(self, binfile):
        """ should be overriden if modifying or has changeable offsets, unpacks the data after header """
        self.data = binfile.readRemaining()
        offsets = []
        for i in range(self._getNumSections()):
            offsets.append(binfile.recall())
        self.offsets = offsets
        binfile.end()

    def _packData(self, binfile):
        """ should be overriden if modifying or has changeable offsets, packs the data after header
            must handle packing the marked offset sections in binfile file
        """
        binfile.writeRemaining(self.data)
        # create the offsets
        for i in self.offsets:
            binfile.writeOffset("I", binfile.unmark(), i)
        binfile.end()

    def _getNumSections(self):
        return self.VERSION_SECTIONCOUNT[self.version]

    def check(self):
        if self.version != self.EXPECTED_VERSION:
            b = Bug(2, 3, '{} {} unusual version {}'.format(self.MAGIC, self.name, self.version),
                    'set to {}'.format(self.EXPECTED_VERSION))
            if self.FORCE_VERSION:
                self.version = self.EXPECTED_VERSION
                b.resolve()
                self.parent.isModified = True

    def _unpack(self, binfile):
        """ unpacks the sub file, subclass must use binfile.end() """
        offset = binfile.start()
        # print('{} {} at {}'.format(self.MAGIC, self.name, offset))
        magic = binfile.readMagic()
        if magic != self.MAGIC:
            raise UnpackingError(binfile, 'Magic {} does not match expected {}'.format(magic, self.MAGIC))
        binfile.readLen()
        self.version, outerOffset = binfile.read("Ii", 8)
        try:
            self.numSections = self._getNumSections()
        except ValueError:
            raise UnpackingError(binfile, "{} {} unsupported version {}".format(self.MAGIC, self.name, self.version))
        binfile.store(self.numSections)  # store section offsets
        self.name = binfile.unpack_name()

    def _pack(self, binfile):
        """ packs sub file into binfile, subclass must use binfile.end() """
        binfile.start()
        binfile.writeMagic(self.MAGIC)
        binfile.markLen()
        binfile.write("Ii", self.version, binfile.getOuterOffset())
        # mark section offsets to be added later
        binfile.mark(self._getNumSections())
        # name offset to be packed separately
        binfile.storeNameRef(self.name)

    def save(self, dest, overwrite):
        if dest is None:
            dest = self.name
            ext = '.' + self.EXT
            if not dest.endswith(ext):
                dest += ext
        if os.path.exists(dest) and not overwrite and not self.OVERWRITE_MODE:
            AUTO_FIXER.error('{} already exists!'.format(dest))
            return
        bin = BinFile(dest, 'w')
        self.pack(bin)
        bin.commitWrite()
        return dest
