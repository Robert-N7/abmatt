"""Tex0 subfile"""
import os
import shutil
import subprocess
import uuid
from math import log

from autofix import AutoFix, Bug
from abmatt.brres.lib.binfile import BinFile
from abmatt.brres.lib.matching import parseValStr, validInt
from abmatt.brres.subfile import SubFile
from brres.lib.packing.pack_tex0 import PackTex0
from brres.lib.unpacking.unpack_tex0 import UnpackTex0


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
            ImgConverter().convert(self, fmt)
            self.mark_modified()

    def set_mipmap_count(self, count):
        if count != self.num_mips:
            ImgConverter().set_mipmap_count(self, count)
            self.mark_modified()

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
        self.mark_modified()

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
            ImgConverter().set_dimensions(self, width, height)
            self.mark_modified()

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
            self.set_dimensions(width, height)
            b.resolve()

    def unpack(self, binfile):
        UnpackTex0(self, binfile)

    def pack(self, binfile):
        PackTex0(self, binfile)

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
    OVERWRITE_IMAGES = False
    tmp_dir = None

    def __init__(self, converter):
        self.converter = converter

    def set_tmp_dir(self, tmp_dir):
        ImgConverterI.tmp_dir = tmp_dir
        self.temp_dest = os.path.join(tmp_dir, 'abmatt_tmp')

    def _get_tmp_dir_name(self):
        return os.path.join(self.tmp_dir, str(uuid.uuid4()))

    def _move_to_temp_dir(self, files=[], tmp_dir=None):
        if tmp_dir is None:
            tmp_dir = self._get_tmp_dir_name()
        os.mkdir(tmp_dir)
        for file in files:
            shutil.copy(file, tmp_dir)
        os.chdir(tmp_dir)
        return tmp_dir

    @staticmethod
    def _move_out_of_temp_dir(tmp_dir, files=[]):
        parent_dir = '..'
        for file in files:
            shutil.move(file, parent_dir)
        os.chdir(parent_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def encode(self, img_file, tex_format, num_mips=-1, check=False):
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
            AutoFix.get().warn('Invalid config value {} for "img_resample", using {}'.format(sample,
                                                                                             filters[
                                                                                                 ImgConverterI.RESAMPLE]))

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
            # if program:
            #     self.temp_dest = os.path.join(self.tmp_dir, 'abmatt_tmp')
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
                with Image.open(img_file) as im:
                    new_file = os.path.join(dir, name + '.png')
                    im.save(new_file)
                if remove_old:
                    os.remove(img_file)
                img_file = new_file
            return img_file, name

        def check_image_dimensions(self, image_file):
            from PIL import Image
            with Image.open(image_file) as im:
                width, height = im.size
                if width > Tex0.MAX_IMG_SIZE or height > Tex0.MAX_IMG_SIZE:
                    new_width, new_height = Tex0.get_scaled_size(width, height)
                    b = Bug(2, 2, f'Texture {image_file} too large ({width}x{height}).',
                            f'Resize to {new_width}x{new_height}.')
                    im = im.resize((new_width, new_height), self.RESAMPLE)
                    im.save(image_file)
                    b.resolve()
                elif not Tex0.is_power_of_two(width) or not Tex0.is_power_of_two(height):
                    new_width = Tex0.nearest_power_of_two(width)
                    new_height = Tex0.nearest_power_of_two(height)
                    b = Bug(2, 2, f'Texture {image_file} not a power of 2 ({width}x{height})',
                            f'Resize to {new_width}x{new_height}')
                    im = im.resize((new_width, new_height), self.RESAMPLE)
                    im.save(image_file)
                    b.resolve()
            return im

        def encode(self, img_file, brres, tex_format=None, num_mips=-1, check=False, overwrite=None):
            if overwrite is None:
                overwrite = self.OVERWRITE_IMAGES
            img_file, name = self.convert_png(self.find_file(img_file))
            if not overwrite and brres is not None and name in brres.get_texture_map():
                AutoFix.get().warn(f'Tex0 {name} already exists!')
                return None
            if check:
                self.check_image_dimensions(img_file)
            # encode
            mips = '--n-mm=' + str(num_mips) if num_mips >= 0 else '--n-mm=auto'
            if not tex_format:
                tex_format = self.IMG_FORMAT
            result = subprocess.call([self.converter, 'encode', img_file, '-d',
                                      self.temp_dest, '-x', tex_format, mips, '-qo'])
            if result:
                raise EncodeError('Failed to encode {}'.format(img_file))
            t = Tex0(name, brres, BinFile(self.temp_dest))
            if brres is not None:
                brres.add_tex0(t)
            os.remove(self.temp_dest)
            t.name = name
            return t

        def batch_encode(self, files, brres, tex_format=None, num_mips=-1, check=False, overwrite=None):
            """Batch encode, faster than single encode when doing multiple files"""
            if overwrite is None:
                overwrite = self.OVERWRITE_IMAGES
            mips = '--n-mm=' + str(num_mips) if num_mips >= 0 else '--n-mm=auto'
            if not tex_format:
                tex_format = self.IMG_FORMAT
            t_files = []
            for x in files:
                try:
                    t_files.append(self.find_file(x))
                except EncodeError:
                    AutoFix.get().warn('Failed to find image {}'.format(x))
            # tmp = 'abmatt-tmp'
            # create a new dir to work in
            tmp = self._move_to_temp_dir(t_files)
            t_files = [os.path.basename(x) for x in t_files]
            path_set = set()
            textures = brres.get_texture_map()
            for x in t_files:
                path, name = self.convert_png(x, remove_old=True)
                if overwrite or name not in textures:
                    path_set.add(path)
                else:
                    os.remove(path)
            if not len(path_set):
                self._move_out_of_temp_dir(tmp)
                return None
            if check:
                for x in path_set:
                    self.check_image_dimensions(x)
            args = [self.converter, '-x', tex_format, mips, '-qo', 'encode']
            args.extend(list(path_set))
            result = subprocess.call(args)
            if result:
                self._move_out_of_temp_dir(tmp)
                raise EncodeError('Failed to encode images {}'.format(files))
            tex0s = []
            new_files = os.listdir()
            for x in new_files:
                if x not in path_set:
                    t = Tex0(x, brres, BinFile(x))
                    tex0s.append(t)
                    brres.add_tex0(t)
            self._move_out_of_temp_dir(tmp)  # cleanup
            return tex0s

        def decode(self, tex0, dest_file, overwrite=None):
            if overwrite is None:
                overwrite = self.OVERWRITE_IMAGES
            if not dest_file:
                dest_file = tex0.name + '.png'
            elif os.path.isdir(dest_file):
                dest_file = os.path.join(dest_file, tex0.name + '.png')
            elif os.path.splitext(os.path.basename(dest_file))[1].lower() != '.png':
                dest_file += '.png'
            if not overwrite and os.path.exists(dest_file):
                AutoFix.get().warn('File {} already exists!'.format(dest_file))
                return None
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

        def batch_decode(self, tex0s, dest_dir=None, overwrite=None):
            if not tex0s:
                return
            if overwrite is None:
                overwrite = self.OVERWRITE_IMAGES
            tmp = os.getcwd()
            use_temp_dir = True
            if dest_dir is not None:
                if not os.path.exists(dest_dir):
                    os.mkdir(dest_dir)
                    use_temp_dir = False
                os.chdir(dest_dir)
            files = []
            for tex in tex0s:
                name = tex.name
                if overwrite or not os.path.exists(name + '.png'):
                    f = BinFile(name, 'w')
                    tex.pack(f)
                    files.append(f)
            if not files:  # our work is already done!
                return files
            if use_temp_dir:  # use a temporary directory if this one already has stuff
                tmp_dir = self._move_to_temp_dir()
            for x in files:
                x.commitWrite()
            args = [self.converter, '--no-mipmaps', '-qo', 'decode']
            args.extend([x.filename for x in files])
            result = subprocess.call(args)
            if result:
                if use_temp_dir:
                    self._move_out_of_temp_dir(tmp_dir)
                raise DecodeError('Failed to decode images')
            for x in files:
                try:
                    os.remove(x.filename)
                except FileNotFoundError:
                    pass
            files = os.listdir()
            if use_temp_dir:
                self._move_out_of_temp_dir(tmp_dir, files)
            os.chdir(tmp)
            return files

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
            fname = self.decode(tex0, self.temp_dest, overwrite=True)
            tex = self.encode(fname, tex0.parent, tex0.get_str(tex0.format), mip_count, overwrite=True)

        def set_dimensions(self, tex0, width, height):
            tmp = self.decode(tex0, 'tmp.png', overwrite=True)
            from PIL import Image
            with Image.open(tmp) as im:
                self.resize_image(im, width, height, tmp)
            tex = self.encode(tmp, tex0.parent, tex0.get_str(tex0.format), overwrite=True)
            os.remove(tmp)
            return tex0

    def __getattr__(self, item):
        if not self.INSTANCE:
            raise NoImgConverterError()
        return getattr(self.INSTANCE, item)

    def __bool__(self):
        return bool(self.INSTANCE)
