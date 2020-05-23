''' BRRES Subfiles '''
import bin

# --------------------------------------------------------
# Most Brres Subfiles
# --------------------------------------------------------
class SubFile():
    '''
    Brres Sub file Class
    classes must implement the following:
    vars: MAGIC, VERSION_SECTIONCOUNT
    functions: [byteSize, unpackData, packData]
    '''
    def __init__(self, name, parent):
        ''' initialize with parent of this file '''
        self.name = name
        self.parent = parent

    def byteSize(self):
        ''' should be overriden if size changes '''
        return self.len

    def unpackData(self, bin):
        ''' Can be overriden, unpacks the data after header '''
        remaining = self.len - (bin.offset - bin.start)
        self.data = bin.read("{}B".format(remaining), remaining)
        # Grab all the section offsets
        self.offsets = bin.recallAll()

    def packData(self, bin):
        ''' Can be overriden, packs the data after header
            must handle packing the marked offset sections in bin file
        '''
        remaining = self.len - (bin.offset - bin.start)
        bin.write("{}B".format(remaining), remaining, self.data)
        for i in range(len(self.offsets)):
            bin.offset = self.offsets[i] + bin.start
            bin.createRef()


    def getNumSections(self):
        if self.numSections:
            return self.numSections
        try:
            return self.VERSION_SECTIONCOUNT[self.version]
        except:
            raise("Unsupported version {} for {}".format(self.version, self.MAGIC))


    def unpack(self, bin):
        ''' unpacks the sub file '''
        bin.start()
        magic = bin.readMagic()
        assert(magic == self.MAGIC)
        self.len, self.version, outerOffset = bin.read("2Ii", 12)
        self.numSections = self.getNumSections()
        bin.store(self.numSections) # store section offsets
        self.name = bin.unpack_name()
        self.unpackData(bin)
        bin.end()

    def pack(self, bin):
        ''' packs sub file into bin '''
        bin.start()
        len = self.byteSize()
        bin.write("4s2Ii", 16, self.MAGIC, len, self.version, bin.getOuterOffset())
        # mark section offsets to be added later
        bin.mark(self.getNumSections())
        # name offset to be packed separately
        bin.storeNameRef(self.name)
        self.packData(bin)
        bin.end()


'''
Chr0 Brres subfile
'''
class Chr(SubFile):
    ''' Chr0 class representation '''
    MAGIC = "chr0"
    VERSION_SECTIONCOUNT = {5:2, 3:1}

'''
Clr0 Brres subfile
'''
class Clr(SubFile):
    ''' Clr0 class '''
    MAGIC = "clr0"
    VERSION_SECTIONCOUNT = {4:2}


'''
Pat0 Brres subfile
'''
class Pat(SubFile):
    ''' Pat0 animation class '''
    MAGIC = "pat0"
    VERSION_SECTIONCOUNT = {4:6}

'''
Scn0 Brres subfile
'''
class Scn(SubFile):
    MAGIC = "scn0"
    VERSION_SECTIONCOUNT = {4:6, 5:7}

'''
Shp0 Brres subfile
'''
class Shp(SubFile):
    MAGIC = "shp0"
    VERSION_SECTIONCOUNT = {4:3}

'''
Tex0 texture file representation
'''
class Tex(SubFile):
    ''' Tex Class '''
    MAGIC = 'tex0'
    VERSION_SECTIONCOUNT = {1:1, 2:2, 3:1}

    # def unpackData(self, bin):
    #     ''' Unpacks tex0 from bin '''
    #     super()._unpack(bin)
    #     # Header
    #     uk, pixelWidth, pixelHeight, format = bin.read("I2HI", 12)
    #     self.numImages, uk, self.numMipmaps, uk = bin.read("2IfI", 16)
    #     remaining = self.len - (bin.offset - bin.start)
    #     # todo? possibly unpack the data in specified format?
    #     self.data = bin.read("{}B".format(remaining), remaining)
    #     bin.end()
