import os
import time

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres.mdl0.material import material
from abmatt.image_converter import EncodeError, NoImgConverterError, ImgConverter
from abmatt.converters.matrix import matrix_to_srt
from abmatt.brres import Brres
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.converters import matrix
from abmatt.converters.influence import decode_mdl0_influences


class Converter:
    NoNormals = 0x1
    NoColors = 0x2
    DETECT_FILE_UNITS = True
    OVERWRITE_IMAGES = False

    class ConvertError(Exception):
        pass

    def _start_saving(self, mdl0):
        AutoFix.get().info('Exporting to {}...'.format(self.mdl_file))
        self.start = time.time()
        if not mdl0:
            self.mdl0 = mdl0 = self.brres.models[0]
        self.cwd = os.getcwd()
        dir, name = os.path.split(self.mdl_file)
        if dir:
            os.chdir(dir)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.influences = decode_mdl0_influences(mdl0)
        self.tex0_map = {}
        return base_name, mdl0

    def _end_saving(self, writer):
        self._create_image_library(self.tex0_map.values())
        os.chdir(self.cwd)
        writer.write(self.mdl_file)
        AutoFix.get().info('\t...finished in {} seconds.'.format(round(time.time() - self.start, 2)))

    def _start_loading(self, model_name):
        AutoFix.get().info('Converting {}... '.format(self.mdl_file))
        self.start = time.time()
        self.cwd = os.getcwd()
        self.mdl_file = os.path.abspath(self.mdl_file)
        self.material_library = Brres.get_material_library()
        brres_dir, brres_name = os.path.split(self.brres.name)
        base_name = os.path.splitext(brres_name)[0]
        self.is_map = True if 'map' in base_name else False
        dir, name = os.path.split(self.mdl_file)
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
        AutoFix.get().info('\t... finished in {} secs'.format(round(time.time() - self.start, 2)))
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
        scale, rotation, translation = matrix_to_srt(matrix)
        bone.scale = scale
        bone.fixed_scale = np.allclose(scale, 1)
        bone.scale_equal = scale[2] == scale[1] == scale[0]
        bone.rotation = rotation
        bone.fixed_rotation = np.allclose(rotation, 0)
        bone.translation = translation
        bone.fixed_translation = np.allclose(translation, 0)

    @staticmethod
    def is_identity_matrix(mtx):
        return np.allclose(mtx, matrix.IDENTITY)

    def _encode_material(self, generic_mat):
        if self.replacement_model:
            m = self.replacement_model.get_material_by_name(generic_mat.name)
            if m is None:
                m = self.material_library.get(generic_mat)
            if m is not None:
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

    def _create_image_library(self, tex0s):
        if not tex0s:
            return True
        converter = ImgConverter()
        if not converter:
            AutoFix.get().error('No image converter found!')
            return False
        converter.batch_decode(tex0s, self.image_dir)
        return True

    @staticmethod
    def __normalize_image_path_map(image_path_map):
        normalized = {}
        for x in image_path_map:
            path = image_path_map[x]
            normalized[os.path.splitext(os.path.basename(path))[0]] = path
        normalized.update(image_path_map)
        return normalized

    def _import_images(self, image_path_map):
        normalized = False
        image_paths = {}
        for map in self.image_library:  # only add images that are used
            path = image_path_map.get(map)
            if path is None:
                if not normalized:
                    image_path_map = self.__normalize_image_path_map(image_path_map)
                    path = image_path_map.get(map)
                    normalized = True
                if path is None:
                    continue
            image_paths[map] = path
        try:
            return self._try_import_textures(self.brres, image_paths)
        except NoImgConverterError as e:
            AutoFix.get().exception(e)

    @staticmethod
    def _try_import_textures(brres, image_paths):
        if len(image_paths):
            try:
                converter = ImgConverter()
                converter.batch_encode(image_paths.values(), brres, overwrite=converter.OVERWRITE_IMAGES)
            except EncodeError:
                AutoFix.get().warn('Failed to encode images')
        return image_paths

    def __init__(self, brres, mdl_file, flags=0, encode=True):
        if not brres:
            # filename = Brres.getExpectedBrresFileName(mdl_file)
            d, f = os.path.split(mdl_file)
            filename = os.path.join(d, os.path.splitext(f)[0] + '.brres')
            brres = Brres.get_brres(filename, True)
        self.brres = brres
        self.texture_library = brres.get_texture_map()
        self.mdl_file = mdl_file
        self.mdl0 = None
        self.flags = flags
        self.image_library = set()
        self.replacement_model = None
        self.encode = encode

    def convert(self):
        if self.encode:
            self.load_model()
        else:
            self.save_model()

    def __eq__(self, other):
        if other is None:
            return False
        if self.encode != other.encode:
            return False
        if self.encode:
            return self.mdl_file == other.mdl_file
        else:
            return self.brres == other.brres

    def load_model(self, model_name):
        raise NotImplementedError()

    def save_model(self, mdl0):
        raise NotImplementedError()


def float_to_str(fl):
    return ('%f' % fl).rstrip('0').rstrip('.')
