""" BRRES Subfiles """


# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
from abmatt.binfile import Folder, PackingError, printCollectionHex, UnpackingError
from abmatt.matching import info_default
from abmatt.autofix import AUTO_FIXER, Bug


class SubFile(object):
    """
    Brres Sub file Class
    classes must implement the following:
    vars: MAGIC, VERSION_SECTIONCOUNT
    functions: byteSize, unpack, pack, unpackData, packData
    """
    MAGIC = 'NONE'
    SETTINGS = ('version', 'sections')
    VERSION_SECTIONCOUNT = {}
    EXPECTED_VERSION = 0    # override this

    def __init__(self, name, parent):
        """ initialize with parent of this file """
        self.name = name
        self.parent = parent
        self.version = self.EXPECTED_VERSION

    def __getitem__(self, item):
        if item == self.SETTINGS[0]:
            return self.version
        elif item == self.SETTINGS[1]:
            return self._getNumSections()

    def _byteSize(self):
        """ should be overriden if size changes """
        return self.byte_len

    def _unpackData(self, binfile):
        """ should be overriden if modifying or has changeable offsets, unpacks the data after header """
        self.data = binfile.readRemaining(self.byte_len)
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
        if self.version not in self.VERSION_SECTIONCOUNT:
            raise ("{} {} unsupported version {}".format(self.MAGIC, self.name, self.version))
        return self.VERSION_SECTIONCOUNT[self.version]

    def check(self):
        if self.version != self.EXPECTED_VERSION:
            b = Bug(2, 3, '{} {} unusual version {}'.format(self.MAGIC, self.name, self.version),
                    'set to {}'.format(self.EXPECTED_VERSION))
            if b.should_fix():
                self.version = self.EXPECTED_VERSION
                b.resolve()

    def _unpack(self, binfile):
        """ unpacks the sub file, subclass must use binfile.end() """
        offset = binfile.start()
        # print('{} {} at {}'.format(self.MAGIC, self.name, offset))
        magic = binfile.readMagic()
        if magic != self.MAGIC:
            raise UnpackingError('Magic {} does not match expected {}'.format(magic, self.MAGIC))
        self.byte_len, self.version, outerOffset = binfile.read("2Ii", 12)
        self.numSections = self._getNumSections()
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

    def info(self, key=None, indentation=0):
        info_default(self, '>(' + self.MAGIC + ')' + self.name, key, indentation)

