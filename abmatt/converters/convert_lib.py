import os
import time

from PIL import Image
import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER, Bug
from abmatt.brres.mdl0 import material
from abmatt.brres.tex0 import EncodeError, Tex0, ImgConverterI, NoImgConverterError
from abmatt.converters.matrix import matrix_to_srt
from abmatt.brres.mdl0 import Mdl0


class Converter:
    NoNormals = 0x1
    NoColors = 0x2
    IDENTITY_MATRIX = np.identity(4)
    DETECT_FILE_UNITS = True

    class ConvertError(Exception):
        pass

    def _start_loading(self, model_name):
        AUTO_FIXER.info('Converting {}... '.format(self.mdl_file))
        self.start = time.time()
        self.cwd = os.getcwd()
        self.mdl_file = os.path.abspath(self.mdl_file)
        brres_dir, brres_name = os.path.split(self.brres.name)
        base_name = os.path.splitext(brres_name)[0]
        self.is_map = True if 'map' in base_name else False
        dir, name = os.path.split(self.mdl_file)
        material.Material.WARNINGS_ON = False
        if dir:
            os.chdir(dir)  # change to the dir to help find relative paths
        return self._init_mdl0(brres_name, os.path.splitext(name)[0], model_name)

    def _end_loading(self):
        mdl0 = self.mdl0
        mdl0.rebuild_header()
        self.brres.add_mdl0(mdl0)
        if self.is_map:
            mdl0.add_map_bones()
        os.chdir(self.cwd)
        material.Material.WARNINGS_ON = True
        AUTO_FIXER.info('\t... finished in {} secs'.format(round(time.time() - self.start, 2)))
        return mdl0

    def _init_mdl0(self, brres_name, mdl_name, mdl0_name):
        if mdl0_name is None:
            mdl0_name = self.__get_mdl0_name(brres_name, mdl_name)
        self.replacement_model = self.brres.getModel(mdl0_name)
        self.mdl0 = Mdl0(mdl0_name, self.brres)
        return self.mdl0

    @staticmethod
    def __get_mdl0_name(brres_name, model_name):
        common_models = ('course', 'map', 'vrcorn')
        for x in common_models:
            if x in brres_name or x in model_name:
                return x
        model_name = os.path.splitext(model_name)[0]
        replace = brres_name + '-'
        if model_name.startswith(replace) and len(model_name) > len(replace):
            model_name = model_name[len(replace):]
        return model_name

    @staticmethod
    def set_bone_matrix(bone, matrix):
        """Untested set translation/scale/rotation with matrix"""
        bone.transform_matrix = matrix[:3]  # don't include fourth row
        bone.inverse_matrix = np.linalg.inv(matrix)[:3]
        bone.scale, bone.rotation, bone.translation = matrix_to_srt(matrix)

    @staticmethod
    def is_identity_matrix(matrix):
        return np.allclose(matrix, Converter.IDENTITY_MATRIX)

    def _encode_material(self, generic_mat):
        if self.replacement_model:
            m = self.replacement_model.getMaterialByName(generic_mat.name)
            if m:
                mat = material.Material.get_unique_material(generic_mat.name, self.mdl0)
                self.mdl0.add_material(mat)
                mat.paste(m)
            else:
                mat = generic_mat.encode(self.mdl0)
        else:
            mat = generic_mat.encode(self.mdl0)
        for x in mat.layers:
            self.image_library.add(x.name)
        return mat

    @staticmethod
    def __normalize_image_path_map(image_path_map):
        normalized = {}
        for x in image_path_map:
            path = image_path_map[x]
            normalized[os.path.splitext(os.path.basename(path))[0]] = path
        normalized.update(image_path_map)
        return normalized

    def _import_images(self, image_path_map):
        try:
            normalized = False
            for map in self.image_library:  # only add images that are used
                path = image_path_map.get(map)
                if path is None:
                    if not normalized:
                        image_path_map = self.__normalize_image_path_map(image_path_map)
                        path = image_path_map.get(map)
                        normalized = True
                    if path is None:
                        continue
                self._try_import_texture(self.brres, path, map)
        except NoImgConverterError as e:
            AUTO_FIXER.error(e)

    def _try_import_texture(self, brres, image_path, layer_name=None):
        if not layer_name:
            layer_name = os.path.splitext(os.path.basename(image_path))[0]
        if not brres.hasTexture(layer_name):
            if len(image_path) < 4:
                AUTO_FIXER.warn('Image path {} is not valid'.format(image_path))
                return layer_name
            ext = image_path[-4:].lower()
            # check it if it's the first or if a resize occurred or not correct extension
            if self.is_first_image or self.check_image or ext != '.png':
                self.is_first_image = False
                if image_path.startswith('file://'):
                    image_path = image_path.replace('file://', '')
                if not os.path.exists(image_path):
                    return layer_name
                im = Image.open(image_path)
                modified = False
                if ext != '.png':
                    AUTO_FIXER.info(f'Conversion from {ext} to tex0 not supported, converting to png', 4)
                    dir, name = os.path.split(image_path)
                    image_path = os.path.join(dir, os.path.splitext(name)[0] + '.png')
                    modified = True
                width, height = im.size
                if width > Tex0.MAX_IMG_SIZE or height > Tex0.MAX_IMG_SIZE:
                    new_width, new_height = Tex0.get_scaled_size(width, height)
                    b = Bug(2, 2, f'Texture {layer_name} too large ({width}x{height}).',
                            f'Resize to {new_width}x{new_height}.')
                    dir, name = os.path.split(image_path)
                    base, ext = os.path.splitext(name)
                    image_path = os.path.join(dir, base + '-resized' + ext)
                    im = im.resize((width, height), ImgConverterI.get_resample())
                    modified = True
                    self.check_image = True
                    b.resolve()
                if modified:
                    im.save(image_path)
            try:
                brres.import_texture(image_path, layer_name)
            except EncodeError:
                AUTO_FIXER.warn('Failed to encode image {}'.format(image_path))
        return layer_name

    def __init__(self, brres, mdl_file, flags=0):
        self.brres = brres
        self.mdl_file = mdl_file
        self.mdl0 = None
        self.flags = flags
        self.check_image = False
        self.is_first_image = True
        self.image_library = set()
        self.replacement_model = None

    def load_model(self, model_name):
        raise NotImplementedError()

    def save_model(self, mdl0):
        raise NotImplementedError()


def remap_collection(iterable):
    remap = {}
    item_to_index = {}
    new_index = 0
    for i in range(len(iterable)):
        x = iterable[i]
        index = item_to_index.get(x)
        if index is not None:
            remap[i] = index
        else:
            remap[i] = item_to_index[x] = new_index
            new_index += 1
    new_collection = []


def float_to_str(fl):
    return ('%f' % fl).rstrip('0').rstrip('.')
