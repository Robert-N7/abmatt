import os

from PIL import Image

from brres.lib.binfile import BinFile
from brres.tex0 import Tex0


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
        super(NoImgConverterError, self).__init__(msg)


class ImgConverterI:
    IMG_FORMAT = 'cmpr'
    IMG_RESAMPLE = Image.BICUBIC

    def __init__(self, converter):
        self.converter = converter

    @staticmethod
    def set_image_resample(sample):
        if sample:
            samples = ['nearest', 'lanczos', 'bilinear', 'bicubic', 'box', 'hamming']
            i = samples.index(sample)
            ImgConverterI.IMG_RESAMPLE = i

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
            program = 'wimgt'
            if which(program):
                self.temp_dest = 'tmp.tex0'
            else:
                program = None
            super(ImgConverter.Wimgt, self).__init__(program)

        def encode(self, img_file, tex_format=None, num_mips=-1):
            # encode
            dir, fname = os.path.split(img_file)
            name = os.path.splitext(fname)[0]
            mips = str(num_mips) if num_mips >= 0 else 'auto'
            if not tex_format:
                tex_format = self.IMG_FORMAT
            result = os.system(
                '{} encode {} -d {} -x {} -q --n-mm={} -o'.format(self.converter, img_file, self.temp_dest, tex_format,
                                                               mips))
            if result:
                raise EncodeError('Failed to encode {}'.format(img_file))
            t = Tex0(name, None, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            t.name = name
            return t

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
            result = os.system('{} decode {} -q -d {} --no-mipmaps -o'.format(self.converter, self.temp_dest, dest_file))
            if self.temp_dest != dest_file:
                os.remove(self.temp_dest)
            if result:
                raise DecodeError('Failed to decode {}'.format(tex0.name))
            return dest_file

        def convert(self, tex0, tex_format):
            f = BinFile(self.temp_dest, 'w')
            tex0.pack(f)
            f.commitWrite()
            result = os.system('{} encode {} -o -q -x {}'.format(self.converter, self.temp_dest, tex_format))
            if result:
                raise EncodeError('Failed to encode {}'.format(tex0.name))
            t = Tex0(tex0.name, tex0.parent, BinFile(self.temp_dest))
            os.remove(self.temp_dest)
            return t

        def set_mipmap_count(self, tex0, mip_count=-1):
            fname = self.decode(tex0, self.temp_dest)
            tex = self.encode(fname, tex0.format, mip_count)
            tex0.paste(tex)

        def set_dimensions(self, tex0, width, height):
            fname = self.decode(tex0, self.temp_dest)
            im = Image.open(fname)
            im = im.resize((width, height), self.IMG_RESAMPLE)
            im.save(fname)
            tex = self.encode(fname, tex0.get_str('format'))
            os.remove(fname)
            tex0.paste(tex)

    def __getattr__(self, item):
        if not self.INSTANCE:
            raise NoImgConverterError()
        return getattr(self.INSTANCE, item)

    def __bool__(self):
        return bool(self.INSTANCE)
