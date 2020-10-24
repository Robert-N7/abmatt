"""Tex0 subfile"""
from math import log

from abmatt.autofix import Bug, AutoFix
from abmatt.brres.lib.matching import parseValStr, validInt
from abmatt.brres.subfile import SubFile
from abmatt.brres.lib.packing.pack_tex0 import PackTex0
from abmatt.brres.lib.unpacking.unpack_tex0 import UnpackTex0


class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    EXT = 'tex0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3
    RESIZE_TO_POW_TWO = False
    MAX_IMG_SIZE = 1024
    converter = None   # store a ref to image converter
    SETTINGS = ('dimensions', 'format', 'mipmapcount', 'name')
    FORMATS = {0: 'I4', 1: 'I8', 2: 'IA4', 3: 'IA8',
               4: 'RGB565', 5: 'RGB5A3', 6: 'RGBA32',
               8: 'C4', 9: 'C8', 10: 'C14X2', 14: 'CMPR'}

    def __init__(self, name, parent=None, binfile=None):
        super(Tex0, self).__init__(name, parent, binfile)

    @staticmethod
    def set_max_image_size(size):
        Tex0.MAX_IMG_SIZE = size if Tex0.is_power_of_two(size) else Tex0.lower_power_of_two(size)

    def begin(self):
        self.width = 0
        self.height = 0
        self.format = 0
        self.num_images = 0
        self.num_mips = 0
        self.data = None

    def get_str(self, key):
        if key == 'dimensions':
            return self.width, self.height
        elif key == 'format':
            return self.FORMATS[self.format]
        elif key == 'mipmapcount':
            return self.num_mips
        elif key == 'name':
            return self.name

    def set_str(self, key, value):
        if key == 'dimensions':
            width, height = parseValStr(value)
            width = validInt(width, 1, self.MAX_IMG_SIZE + 1)
            height = validInt(height, 1, self.MAX_IMG_SIZE + 1)
            self.set_dimensions(width, height)
        elif key == 'format':
            return self.set_format(value)
        elif key == 'mipmapcount':
            return self.set_mipmap_count(validInt(value, 0, 20))
        elif key == 'name':
            return self.parent.rename_texture(value)

    def set_format(self, fmt):
        if fmt != self.format:
            if fmt.upper() not in self.FORMATS.values():
                raise ValueError('Invalid tex0 format {}'.format(fmt))
            if self.converter:
                self.converter.convert(self, fmt)
                self.mark_modified()
                return True
        return False

    def set_mipmap_count(self, count):
        if count != self.num_mips:
            if self.converter:
                self.converter.set_mipmap_count(self, count)
                self.mark_modified()
                return True
        return False

    @staticmethod
    def is_power_of_two(n):
        return n & (n - 1) == 0

    @staticmethod
    def nearest_power_of_two(v):
        return pow(2, round(log(v) / log(2)))

    @staticmethod
    def lower_power_of_two(v):
        return pow(2, log(v) // log(2))

    def set_power_of_two(self):
        width = self.width if self.is_power_of_two(self.width) else self.nearest_power_of_two(self.width)
        height = self.height if self.is_power_of_two(self.height) else self.nearest_power_of_two(self.height)
        if self.converter:
            self.converter.set_dimensions(self, width, height)
            self.mark_modified()
            return True
        return False

    def paste(self, item):
        self.width = item.width
        self.height = item.height
        self.format = item.format
        self.num_images = item.num_images
        self.num_mips = item.num_mips
        self.data = item.data
        self.mark_modified()

    def should_resize_pow_two(self):
        return self.RESIZE_TO_POW_TWO

    def __str__(self):
        return f'TEX0 {self.name} {self.width}x{self.height} ({self.FORMATS[self.format]})'

    @staticmethod
    def get_scaled_size(width, height):
        highest = max(width, height)
        ratio = highest / Tex0.MAX_IMG_SIZE
        if highest == height:
            width = Tex0.nearest_power_of_two(width / ratio)
            height = Tex0.MAX_IMG_SIZE
        else:
            height = Tex0.nearest_power_of_two(height / ratio)
            width = Tex0.MAX_IMG_SIZE
        return width, height

    def set_dimensions(self, width, height):
        if width != self.width or height != self.height:
            if self.converter:
                self.converter.set_dimensions(self, width, height)
                self.mark_modified()
                return True
        return False

    def check(self):
        super(Tex0, self).check()
        if not self.is_power_of_two(self.width) or not self.is_power_of_two(self.height):
            b = Bug(2, 2, str(self) + ' not a power of 2', None)
            if self.should_resize_pow_two():
                if self.set_power_of_two():
                    b.fix_des = 'Resize to {}x{}'.format(self.width, self.height)
                    b.resolve()
        if self.width > self.MAX_IMG_SIZE or self.height > self.MAX_IMG_SIZE:
            width, height = self.get_scaled_size(self.width, self.height)
            b = Bug(2, 2, str(self) + ' is too large', f'resize to {width}x{height}')
            if self.set_dimensions(width, height):
                b.resolve()

    def unpack(self, binfile):
        UnpackTex0(self, binfile)

    def pack(self, binfile):
        PackTex0(self, binfile)

    def info(self, key=None, indentation=0):
        AutoFix.get().info('{} {}: {} {}x{} mips:{}'.format(self.MAGIC, self.name, self.FORMATS[self.format],
                                               self.width, self.height, self.num_mips), 1)


