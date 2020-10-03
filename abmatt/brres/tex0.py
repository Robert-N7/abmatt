"""Tex0 subfile"""
import os
import shutil
import subprocess
from math import log

from abmatt.brres.lib.autofix import AUTO_FIXER, Bug
from abmatt.brres.lib.binfile import BinFile
from abmatt.brres.lib.matching import parseValStr, validInt
from abmatt.brres.subfile import SubFile


class Tex0(SubFile):
    """ Tex0 Class """
    MAGIC = 'TEX0'
    EXT = 'tex0'
    VERSION_SECTIONCOUNT = {1: 1, 2: 2, 3: 1}
    EXPECTED_VERSION = 3
    RESIZE_TO_POW_TWO = False
    MAX_IMG_SIZE = 1024
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
            ImgConverter().set_dimensions(self, width, height)
        elif key == 'format':
            return self.set_format(value)
        elif key == 'mipmapcount':
            return self.set_mipmap_count(validInt(value, 0, 20))
        elif key == 'name':
            return self.set_name(value)

    def set_format(self, fmt):
        if fmt != self.format:
            if fmt.upper() not in self.FORMATS.values():
                raise ValueError('Invalid tex0 format {}'.format(fmt))
            ImgConverter().convert(self, fmt)

    def set_mipmap_count(self, count):
        if count != self.num_mips:
            ImgConverter().set_mipmap_count(self, count)

    def set_name(self, name):
        return self.parent.rename_texture(self, name)

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
        ImgConverter().set_dimensions(self, width, height)

    def paste(self, item):
        self.width = item.width
        self.height = item.height
        self.format = item.format
        self.num_images = item.num_images
        self.num_mips = item.num_mips
        self.data = item.data

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

    def check(self):
        super(Tex0, self).check()
        if not self.is_power_of_two(self.width) or not self.is_power_of_two(self.height):
            b = Bug(2, 2, str(self) + ' not a power of 2', None)
            if self.should_resize_pow_two():
                self.set_power_of_two()
                b.fix_des = 'Resize to {}x{}'.format(self.width, self.height)
                b.resolve()
        if self.width > self.MAX_IMG_SIZE or self.height > self.MAX_IMG_SIZE:
            width, height = self.get_scaled_size(self.width, self.height)
            b = Bug(2, 2, str(self) + ' is too large', f'resize to {width}x{height}')
            ImgConverter().set_dimensions(self, width, height)
            b.resolve()


    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.width, self.height, self.format, self.num_images, _, self.num_mips, _ = binfile.read('I2H3IfI', 0x1c)
        binfile.recall()
        self.data = binfile.readRemaining()
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


def which(program):
    def is_exe(exe_file):
        return os.path.isfile(exe_file) and os.access(exe_file, os.X_OK)

    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, program)
        if is_exe(exe_file):
            return exe_file
        exe_file += '.exe'
        if is_exe(exe_file):
            return exe_file


class EncodeError(Exception):
    def __init__(self, msg=None):
        super(EncodeError, self).__init__(msg)


class DecodeError(Exception):
    def __init__(self, msg=None):
        super(DecodeError, self).__init__(msg)


class NoImgConverterError(Exception):
    def __init__(self, msg=None):
        if not msg:
            msg = 'No image converter!'
        super(NoImgConverterError, self).__init__(msg)


class ImgConverterI:
    IMG_FORMAT = 'cmpr'
    RESAMPLE = 3

    def __init__(self, converter):
        self.converter = converter

    def encode(self, img_file, tex_format, num_mips=-1):
        raise NotImplementedError()

    def decode(self, tex0, dest_file):
        raise NotImplementedError()

    def convert(self, tex0, tex_format):
        raise NotImplementedError()

    def set_mipmap_count(self, tex0, mip_count):
        raise NotImplementedError()

    def set_dimensions(self, tex0, width, height):
        raise NotImplementedError()

    @staticmethod
    def set_resample(sample):
        filters = ['nearest', 'lanczos', 'bilinear', 'bicubic', 'box', 'hamming']
        try:
            sampler_index = filters.index(sample)
            ImgConverterI.RESAMPLE = sampler_index
        except (ValueError, IndexError):
            AUTO_FIXER.warn('Invalid config value {} for "img_resample", using {}'.format(sample,
                                                                                      filters[ImgConverterI.RESAMPLE]))

    @staticmethod
    def get_resample():
        return ImgConverterI.RESAMPLE

    @staticmethod
    def resize_image(img, width, height, img_file_path):
        img = img.resize((width, height), ImgConverterI.get_resample())
        img.save(img_file_path)

    def __bool__(self):
        return self.converter is not None


class ImgConverter:
    INSTANCE = None  # singleton instance

    def __init__(self, converter=None):
        if not self.INSTANCE:
            if not converter:
                converter = self.Wimgt()
            self.INSTANCE = converter
        elif converter:
            self.INSTANCE.converter = converter

    class Wimgt(ImgConverterI):

        def __init__(self):
            program = which('wimgt')
            if program:
                self.temp_dest = 'abmatt_tmp'
            super(ImgConverter.Wimgt, self).__init__(program)

        @staticmethod
        def find_file(filename):
            if filename.startswith('file://'):
                filename = filename.replace('file://', '')
            if not os.path.exists(filename):
                raise EncodeError('No such file {}'.format(filename))
            return filename

        @staticmethod
        def convert_png(img_file, remove_old=False):
            dir, fname = os.path.split(img_file)
            name, ext = os.path.splitext(fname)
            if ext.lower() != '.png':
                from PIL import Image
                im = Image.open(img_file)
                new_file = os.path.join(dir, name + '.png')
                im.save(new_file)
                if remove_old:
                    os.remove(img_file)
                img_file = new_file
            return img_file, name

        def encode(self, img_file, tex_format=None, num_mips=-1):
            img_file, name = self.convert_png(self.find_file(img_file))
            # encode
            mips = '--n-mm=' + str(num_mips) if num_mips >= 0 else ''
            if not tex_format:
                tex_format = self.IMG_FORMAT
            result = subprocess.call([self.converter, 'encode', img_file, '-d',
                                      self.temp_dest, '-x', tex_format, mips, '-qo'])
            if result:
                raise EncodeError('Failed to encode {}'.format(img_file))
            t = Tex0(name, None, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            t.name = name
            return t

        @staticmethod
        def __move_to_temp_dir(files, tmp_dir):
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            os.mkdir(tmp_dir)
            for file in files:
                shutil.copy(file, tmp_dir)
            os.chdir(tmp_dir)
            return os.listdir()

        @staticmethod
        def __move_out_of_temp_dir(tmp_dir):
            os.chdir('..')
            shutil.rmtree(tmp_dir, ignore_errors=True)

        def batch_encode(self, files, tex_format=None, num_mips=-1):
            """Batch encode, faster than single encode when doing multiple files"""
            mips = '--n-mm=' + str(num_mips) if num_mips >= 0 else ''
            if not tex_format:
                tex_format = self.IMG_FORMAT
            t_files = [self.find_file(x) for x in files]
            tmp = 'abmatt-tmp'
            # create a new dir to work in
            t_files = self.__move_to_temp_dir(t_files, tmp)
            t_files = set([self.convert_png(x, remove_old=True)[0] for x in t_files])
            result = subprocess.call([self.converter, 'encode', '*.png',
                                      '-x', tex_format, mips, '-qo'])
            if result:
                self.__move_out_of_temp_dir(tmp)
                raise EncodeError('Failed to encode images {}'.format(files))
            tex0s = []
            new_files = os.listdir()
            for x in new_files:
                if x not in t_files:
                    tex0s.append(Tex0(x, None, BinFile(x)))
            self.__move_out_of_temp_dir(tmp)    # cleanup
            return tex0s

        def decode(self, tex0, dest_file):
            if not dest_file:
                dest_file = tex0.name + '.png'
            elif os.path.isdir(dest_file):
                dest_file = os.path.join(dest_file, tex0.name + '.png')
            elif os.path.splitext(os.path.basename(dest_file))[1].lower() != '.png':
                dest_file += '.png'
            f = BinFile(self.temp_dest, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = subprocess.call([self.converter, 'decode', self.temp_dest,
                                      '-d', dest_file, '--no-mipmaps', '-qo'])
            if self.temp_dest != dest_file:
                os.remove(self.temp_dest)
            if result:
                raise DecodeError('Failed to decode {}'.format(tex0.name))
            return dest_file

        def batch_decode(self, tex0s, dest_dir=None):
            pass

        def convert(self, tex0, tex_format):
            f = BinFile(self.temp_dest, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = subprocess.call([self.converter, 'encode', self.temp_dest, '-oq', '-x', tex_format])
            if result:
                os.remove(self.temp_dest)
                raise EncodeError('Failed to encode {}'.format(tex0.name))
            t = Tex0(tex0.name, tex0.parent, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            return t

        def set_mipmap_count(self, tex0, mip_count=-1):
            fname = self.decode(tex0, self.temp_dest)
            tex = self.encode(fname, tex0.format, mip_count)
            tex0.paste(tex)

        def set_dimensions(self, tex0, width, height):
            tmp = self.decode(tex0, 'tmp.png')
            from PIL import Image
            self.resize_image(Image.open(tmp), width, height, tmp)
            tex = self.encode(tmp, tex0.get_str(tex0.format))
            os.remove(tmp)
            tex0.paste(tex)
            return tex0

    def __getattr__(self, item):
        if not self.INSTANCE:
            raise NoImgConverterError()
        return getattr(self.INSTANCE, item)

    def __bool__(self):
        return bool(self.INSTANCE)
