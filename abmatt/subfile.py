""" BRRES Subfiles """

# Todo, parse all name references so the offsets can be properly updated to the new string table

# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
from abmatt.binfile import Folder, PackingError


class SubFile(object):
    """
    Brres Sub file Class
    classes must implement the following:
    vars: MAGIC, VERSION_SECTIONCOUNT
    functions: byteSize, unpack, pack, unpackData, packData
    """
    MAGIC = 'NONE'
    VERSION_SECTIONCOUNT = {}

    def __init__(self, name, parent):
        """ initialize with parent of this file """
        self.name = name
        self.parent = parent

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
        try:
            return self.VERSION_SECTIONCOUNT[self.version]
        except:
            raise ("Unsupported version {} for {}".format(self.version, self.MAGIC))

    def _unpack(self, binfile):
        """ unpacks the sub file, subclass must use binfile.end() """
        binfile.start()
        magic = binfile.readMagic()
        assert (magic == self.MAGIC)
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

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + self.name if indentation_level else '>' + self.parent.name + '->' + self.name
        print('{}: {} v{}\tbyte_size {}'.format(trace, self.MAGIC, self.version, self._byteSize()))


'''
Chr0 Brres subfile
'''


class Chr0(SubFile):
    """ Chr0 class representation """
    MAGIC = "CHR0"
    VERSION_SECTIONCOUNT = {5: 2, 3: 1}

    def __init__(self, name, parent):
        super(Chr0, self).__init__(name, parent)
        self.animations = []

    class ModelAnim:
        def __init__(self, name, offset):
            self.name = name
            self.offset = offset  # since we don't parse data... store name offsetg

    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.framecount, self.size, self.loop, _ = binfile.read('I2H2I', 16)
        binfile.recall()  # section 0
        f = Folder(binfile, 'chr0root')
        f.unpack(binfile)
        self.data = binfile.readRemaining(self.byte_len)
        while len(f):
            name = f.recallEntryI()
            self.animations.append(self.ModelAnim(name, binfile.offset - binfile.beginOffset))

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I2H2I', 0, self.framecount, self.size, self.loop, 0)
        f = Folder(binfile, 'chr0root')
        for x in self.animations:
            f.addEntry(x.name)
        binfile.createRef()
        f.pack(binfile)
        binfile.writeRemaining(self.data)
        for x in self.animations:  # hackish way of overwriting the string offsets
            binfile.offset = binfile.beginOffset + x.offset
            f.createEntryRefI()
            binfile.storeNameRef(x.name)
        binfile.end()


'''
Clr0 Brres subfile
'''


class Clr0(SubFile):
    """ Clr0 class """
    MAGIC = "CLR0"
    VERSION_SECTIONCOUNT = {4: 2}

    def __init__(self, name, parent):
        super(Clr0, self).__init__(name, parent)

    def unpack(self, binfile):
        print('Warning: Clr0 not supported, unable to edit')
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        raise PackingError(binfile, 'Packing clr0 files not supported')
        self._pack(binfile)
        self._unpackData(binfile)


'''
Scn0 Brres subfile
'''


class Scn0(SubFile):
    MAGIC = "SCN0"
    VERSION_SECTIONCOUNT = {4: 6, 5: 7}

    def __init__(self, name, parent):
        super(Scn0, self).__init__(name, parent)

    def unpack(self, binfile):
        print('Warning: Scn0 not supported, unable to edit')
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        raise PackingError(binfile, 'Packing scn0 not supported')
        self._pack(binfile)
        self._unpackData(binfile)


'''
Shp0 Brres subfile
'''


class Shp0(SubFile):
    MAGIC = "SHP0"
    VERSION_SECTIONCOUNT = {4: 3}

    def __init__(self, name, parent):
        super(Shp0, self).__init__(name, parent)

    def unpack(self, binfile):
        print('Warning: Shp0 not supported, unable to edit')
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        raise PackingError(binfile, 'SHP0 not supported!')   # because of names
        self._pack(binfile)
        self._unpackData(binfile)


'''
Tex0 texture file representation
'''


class Tex0(SubFile):
    """ Tex Class """
    MAGIC = 'TEX0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}

    def __init__(self, name, parent):
        super(Tex0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._packData(binfile)

    # def unpackData(self, binfile):
    #     ''' Unpacks tex0 from binfile '''
    #     super(SubFile)()._unpack(binfile)
    #     # Header
    #     uk, pixelWidth, pixelHeight, format = binfile.read("I2HI", 12)
    #     self.numImages, uk, self.numMipmaps, uk = binfile.read("2IfI", 16)
    #     remaining = self.len - (binfile.offset - binfile.start)
    #     # todo? possibly unpack the data in specified format?
    #     self.data = binfile.read("{}B".format(remaining), remaining)
    #     binfile.end()
