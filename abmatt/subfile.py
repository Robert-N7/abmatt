''' BRRES Subfiles '''
import binfile

# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
class SubFile(object):
    '''
    Brres Sub file Class
    classes must implement the following:
    vars: MAGIC, VERSION_SECTIONCOUNT
    functions: byteSize, unpack, pack, unpackData, packData
    '''
    def __init__(self, name, parent):
        ''' initialize with parent of this file '''
        self.name = name
        self.parent = parent
        if __debug__:
            print("Creating subfile {}".format(name))

    def _byteSize(self):
        ''' should be overriden if size changes '''
        return self.len

    def _unpackData(self, binfile):
        ''' should be overriden if modifying or has changeable offsets, unpacks the data after header '''
        self.data = binfile.readRemaining(self.byte_len)
        offsets = []
        for i in range(self._getNumSections()):
            offsets.append(binfile.recall())
        self.offsets = offsets
        binfile.end()

    def _packData(self, binfile):
        ''' should be overriden if modifying or has changeable offsets, packs the data after header
            must handle packing the marked offset sections in binfile file
        '''
        binfile.writeRemaining(self.data)
        # create the offsets
        for i in self.offsets:
            binfile.writeOffset("I", binfile.unmark(), i)
        binfile.end()


    def _getNumSections(self):
        try:
            return self.VERSION_SECTIONCOUNT[self.version]
        except:
            raise("Unsupported version {} for {}".format(self.version, self.MAGIC))


    def _unpack(self, binfile):
        ''' unpacks the sub file, subclass must use binfile.end() '''
        binfile.start()
        magic = binfile.readMagic()
        assert(magic == self.MAGIC)
        self.byte_len, self.version, outerOffset = binfile.read("2Ii", 12)
        self.numSections = self._getNumSections()
        binfile.store(self.numSections) # store section offsets
        self.name = binfile.unpack_name()
        if __debug__:
            print("Unpacking {} {} len {} v{} at offset {}".format(magic,
                self.name, self.byte_len, self.version, binfile.offset))

    def _pack(self, binfile):
        ''' packs sub file into binfile, subclass must use binfile.end() '''
        binfile.start()
        binfile.writeMagic(self.MAGIC)
        binfile.markLen()
        binfile.write("Ii", self.version, binfile.getOuterOffset())
        # mark section offsets to be added later
        binfile.mark(self._getNumSections())
        # name offset to be packed separately
        binfile.storeNameRef(self.name)


'''
Chr0 Brres subfile
'''
class Chr0(SubFile):
    ''' Chr0 class representation '''
    MAGIC = "chr0"
    VERSION_SECTIONCOUNT = {5:2, 3:1}
    def __init__(self, name, parent):
        super(Chr0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._unpackData(binfile)




'''
Clr0 Brres subfile
'''
class Clr0(SubFile):
    ''' Clr0 class '''
    MAGIC = "clr0"
    VERSION_SECTIONCOUNT = {4:2}

    def __init__(self, name, parent):
        super(Clr0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._unpackData(binfile)

'''
Pat0 Brres subfile
'''
class Pat0(SubFile):
    ''' Pat0 animation class '''
    MAGIC = "PAT0"
    VERSION_SECTIONCOUNT = {4:6}
    def __init__(self, name, parent):
        super(Pat0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._packData(binfile)

'''
Scn0 Brres subfile
'''
class Scn0(SubFile):
    MAGIC = "scn0"
    VERSION_SECTIONCOUNT = {4:6, 5:7}
    def __init__(self, name, parent):
        super(Scn0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._unpackData(binfile)

'''
Shp0 Brres subfile
'''
class Shp0(SubFile):
    MAGIC = "shp0"
    VERSION_SECTIONCOUNT = {4:3}
    def __init__(self, name, parent):
        super(Shp0, self).__init__(name, parent)

    def unpack(self, binfile):
        self._unpack(binfile)
        self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        self._unpackData(binfile)

'''
Tex0 texture file representation
'''
class Tex0(SubFile):
    ''' Tex Class '''
    MAGIC = 'TEX0'
    VERSION_SECTIONCOUNT = {1:1, 2:2, 3:1}
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
