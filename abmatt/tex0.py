"""Tex0 subfile"""
from math import log

from PIL import Image

from abmatt.subfile import SubFile
from abmatt.autofix import AUTO_FIXER, Bug

class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3
    FORMATS = {0: 'I4', 1: 'I8', 2: 'IA4', 3: 'IA8',
               4: 'RGB565', 5: 'RGB5A3', 6: 'RGBA32',
               8: 'C4', 9: 'C8', 10: 'C14X2', 14: 'CMPR'}
    MAX_POW_TWO = 1024
    RESAMPLE = Image.NEAREST

    def __init__(self, name, parent):
        super(Tex0, self).__init__(name, parent)

    @staticmethod
    def set_resample(resample):
        if resample == 'nearest':
            Tex0.RESAMPLE = Image.NEAREST
        elif resample == 'bilinear':
            Tex0.RESAMPLE = Image.BILINEAR
        elif resample == 'bicubic':
            Tex0.RESAMPLE = Image.BICUBIC
        elif resample == 'lanczos':
            Tex0.RESAMPLE = Image.LANCZOS
        else:
            AUTO_FIXER.error('Unknown sampler {}'.format(resample))

    @staticmethod
    def is_power_of_two(n):
        return n & (n - 1) == 0

    @staticmethod
    def nearest_power_of_two(v):
        return pow(2, round(log(v)/log(2)))

    def fix_size(self, im, width, height):
        new_width = new_height = 0
        if width > self.MAX_POW_TWO:
            new_width = self.MAX_POW_TWO
        if height > self.MAX_POW_TWO:
            new_height = self.MAX_POW_TWO
        if not self.is_power_of_two(width):
            new_width = self.nearest_power_of_two(width)
        if not self.is_power_of_two(height):
            new_height = self.nearest_power_of_two(height)
        if new_width or new_height:
            if not new_width:
                new_width = width
            if not new_height:
                new_height = height
            b = Bug(2,2,'Invalid image size {}x{}'.format(width, height), 'Resize to {}x{}'.format(new_width, new_height))
            if AUTO_FIXER.should_fix(b):
                im = im.resize()
        return im

    def encode(self, img_file, num_mips):
        pass

    def decode(self, img_file):
        pass

    def check(self):
        super(Tex0, self).check()
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
