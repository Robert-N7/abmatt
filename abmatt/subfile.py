""" BRRES Subfiles """

# Todo, parse all name references so the offsets can be properly updated to the new string table

# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
from abmatt.binfile import Folder, PackingError, printCollectionHex
from abmatt.matching import info_default


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
    LOUDNESS = 2            # Loudness levels, 0 silent, 1 errors/warnings, 2 notes, 3 max

    def __init__(self, name, parent):
        """ initialize with parent of this file """
        self.name = name
        self.parent = parent

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

    def check(self, loudness):
        if self.version != self.EXPECTED_VERSION:
            print('CHECK: {} {} unusual version {}'.format(self.MAGIC, self.name, self.version))

    def _unpack(self, binfile):
        """ unpacks the sub file, subclass must use binfile.end() """
        offset = binfile.start()
        # print('{} {} at {}'.format(self.MAGIC, self.name, offset))
        magic = binfile.readMagic()
        assert magic == self.MAGIC
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

