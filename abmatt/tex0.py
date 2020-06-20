"""Tex0 subfile"""
from abmatt.subfile import SubFile


class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3

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
