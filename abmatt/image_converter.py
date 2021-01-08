import os
import shutil
import subprocess
import uuid

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.binfile import BinFile
from abmatt.brres.tex0 import Tex0


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
    TMP_DIR = None

    def __init__(self, converter):
        self.converter = converter

    def get_tmp_dir(self):
        if not os.path.exists(self.TMP_DIR):
            os.mkdir(self.TMP_DIR)
        return self.TMP_DIR

    def get_temp_dest(self):
        return os.path.join(self.get_tmp_dir(), str(uuid.uuid4()))

    def set_tmp_dir(self, tmp_dir):
        if self.TMP_DIR:
            shutil.rmtree(self.TMP_DIR, ignore_errors=True)
        ImgConverterI.TMP_DIR = os.path.abspath(tmp_dir)

    def _get_tmp_dir_name(self):
        return os.path.join(self.get_tmp_dir(), str(uuid.uuid4()))

    def _move_to_temp_dir(self, files=[], tmp_dir=None):
        if tmp_dir is None:
            tmp_dir = self._get_tmp_dir_name()
        os.mkdir(tmp_dir)
        for file in files:
            shutil.copy(file, tmp_dir)
        # os.chdir(tmp_dir)
        return tmp_dir

    @staticmethod
    def _move_out_of_temp_dir(tmp_dir, files=[]):
        # parent_dir = os.path.join(tmp_dir, '..')
        # for file in files:
        #     shutil.move(os.path.join(tmp_dir, file), parent_dir)
        # os.chdir(parent_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def encode(self, img_file, tex_format, num_mips=-1, check=False):
        raise NotImplementedError()

    def decode(self, tex0, dest_file, overwrite=None, num_mips=0):
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

    def __init__(self, tmp_dir=None, converter=None):
        if not self.INSTANCE:
            if not converter:
                converter = self.Wimgt(tmp_dir)
            self.INSTANCE = converter
        elif converter:
            self.INSTANCE.converter = converter

    class Wimgt(ImgConverterI):

        def __init__(self, tmp_dir=None):
            program = which('wimgt')
            self.cleanup = False
            if program:
                if os.name == 'nt':
                    self.si = subprocess.STARTUPINFO()
                    self.si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                else:
                    self.si = None
                if tmp_dir:
                    self.set_tmp_dir(tmp_dir)
                elif not self.get_tmp_dir():
                    self.set_tmp_dir(os.path.join(os.getcwd(), str(uuid.uuid4())))
                    self.cleanup = True
            super(ImgConverter.Wimgt, self).__init__(program)

        def __del__(self):
            # clean up temp files
            if self.cleanup:
                d = self.get_tmp_dir()
                if d and os.path.exists(d):
                    shutil.rmtree(d, ignore_errors=True)

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
            dest = self.get_temp_dest()
            result = subprocess.call([self.converter, 'encode', img_file, '-d',
                                      dest, '-x', tex_format, mips, '-qo'], startupinfo=self.si)
            if result:
                raise EncodeError('Failed to encode {}'.format(img_file))
            t = Tex0(name, brres, BinFile(dest))
            t.name = name
            if brres is not None:
                brres.add_tex0(t)
            os.remove(dest)
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
                path, name = self.convert_png(os.path.join(tmp, x), remove_old=True)
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
            file_names = [os.path.basename(x) for x in path_set]
            args.extend(file_names)
            result = subprocess.call(args, cwd=tmp, startupinfo=self.si)
            if result:
                self._move_out_of_temp_dir(tmp)
                raise EncodeError('Failed to encode images {}'.format(files))
            tex0s = []
            new_files = [x for x in os.listdir(tmp) if x not in file_names]
            for x in new_files:
                t = Tex0(x, brres, BinFile(os.path.join(tmp, x)))
                tex0s.append(t)
                brres.add_tex0(t)
            self._move_out_of_temp_dir(tmp)  # cleanup
            return tex0s

        def decode(self, tex0, dest_file, overwrite=None, num_mips=0):
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
            tmp = self.get_temp_dest()
            f = BinFile(tmp, 'w')
            tex0.pack(f)
            f.commitWrite()
            if num_mips == 0:
                mips = '--no-mipmaps'
            elif num_mips == -1:
                mips = '--n-mm=auto'
            else:
                mips = '--n-mm=' + str(num_mips)
            result = subprocess.call([self.converter, 'decode', tmp,
                                      '-d', dest_file, mips, '-qo'], startupinfo=self.si)
            if tmp != dest_file:
                os.remove(tmp)
            if result:
                raise DecodeError('Failed to decode {}'.format(tex0.name))
            return dest_file

        def batch_decode(self, tex0s, dest_dir=None, overwrite=None):
            if not tex0s:
                return
            if overwrite is None:
                overwrite = self.OVERWRITE_IMAGES
            use_temp_dir = True
            if dest_dir is not None:
                if not os.path.exists(dest_dir):
                    os.mkdir(dest_dir)
                tmp_dir = dest_dir
                use_temp_dir = False
                # os.chdir(dest_dir)
            if use_temp_dir:  # use a temporary directory if this one already has stuff
                tmp_dir = self._move_to_temp_dir()
            files = []
            base_names = []
            for tex in tex0s:
                name = tex.name
                if overwrite or not os.path.exists(os.path.join(tmp_dir, name + '.png')):
                    f = BinFile(os.path.join(tmp_dir, name), 'w')
                    tex.pack(f)
                    base_names.append(name)
                    files.append(f)
            if not files:  # our work is already done!
                return files
            for x in files:
                x.commitWrite()
            args = [self.converter, '--no-mipmaps', '-qo', 'decode']
            args.extend(base_names)
            result = subprocess.call(args, cwd=tmp_dir, startupinfo=self.si)
            if result:
                if use_temp_dir:
                    self._move_out_of_temp_dir(tmp_dir)
                raise DecodeError('Failed to decode images')
            for x in files:
                try:
                    os.remove(x.filename)
                except FileNotFoundError:
                    pass
            files = os.listdir(tmp_dir)
            if use_temp_dir:
                self._move_out_of_temp_dir(tmp_dir, files)
            return files

        def convert(self, tex0, tex_format):
            tmp = self.get_temp_dest()
            f = BinFile(tmp, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = subprocess.call([self.converter, 'encode', tmp, '-oq', '-x', tex_format], startupinfo=self.si)
            if result:
                os.remove(tmp)
                raise EncodeError('Failed to encode {}'.format(tex0.name))
            t = Tex0(tex0.name, tex0.parent, BinFile(tmp))
            os.remove(tmp)
            return t

        def set_mipmap_count(self, tex0, mip_count=-1):
            fname = self.decode(tex0, None, overwrite=True)
            tex = self.encode(fname, tex0.parent, tex0.get_str(tex0.format), mip_count, overwrite=True)
            os.remove(fname)

        def set_dimensions(self, tex0, width, height):
            tmp = self.decode(tex0, None, overwrite=True)
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