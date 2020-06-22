"""Tex0 subfile"""
from abmatt.subfile import SubFile


class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3
    FORMATS = {0: 'I4', 1: 'I8', 2: 'IA4', 3: 'IA8',
               4: 'RGB565', 5: 'RGB5A3', 6: 'RGBA32',
               8: 'C4', 9: 'C8', 10: 'C14X2', 14: 'CMPR'}

    def __init__(self, name, parent):
        super(Tex0, self).__init__(name, parent)

    @staticmethod
    def is_power_of_two(n):
        return n & (n - 1) == 0

    def check(self, loudness):
        super(Tex0, self).check(loudness)
        if not self.is_power_of_two(self.width) or not self.is_power_of_two(self.height):
            print('CHECK: TEX0 {} not a power of 2'.format(self.name))

    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.width, self.height, self.format, self.num_images, _, self.num_mips, _ = binfile.read('I2H3IfI', 0x1c)
        binfile.recall()
        self.data = binfile.readRemaining(self.byte_len)
        binfile.end()

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I2H3IfI', 0, self.width, self.height, self.format, self.num_images, 0, self.num_mips, 0)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.end()

    def info(self, key=None, indentation=0):
        print('{} {}: {} {}x{} mips:{}'.format(self.MAGIC, self.name, self.FORMATS[self.format],
                                               self.width, self.height, self.num_mips))

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
