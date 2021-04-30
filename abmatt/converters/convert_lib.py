import os
import time

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.matching import fuzzy_match
from abmatt.brres.material_library import MaterialLibrary
from abmatt.brres.mdl0.material import material
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.converters import matrix
from abmatt.converters.convert_mats_to_json import MatsToJsonConverter
from abmatt.converters.influence import decode_mdl0_influences
from abmatt.converters.matrix import matrix_to_srt
from abmatt.image_converter import EncodeError, NoImgConverterError, ImgConverter


class Converter:
    NO_NORMALS = 0x1
    NO_COLORS = 0x2
    SINGLE_BONE = 0x4
    DETECT_FILE_UNITS = True
    OVERWRITE_IMAGES = False

    class ConvertError(Exception):
        pass

    def __init__(self, brres, mdl_file, flags=0, encode=True, mdl0=None, encoder=None):
        if not brres:
            # filename = Brres.getExpectedBrresFileName(mdl_file)
            d, f = os.path.split(mdl_file)
            filename = os.path.join(d, os.path.splitext(f)[0] + '.brres')
            brres = Brres.get_brres(filename, True)
        elif type(brres) == str:
            brres = Brres.get_brres(brres, True)
        self.brres = brres
        self.texture_library = brres.get_texture_map()
        self.mdl_file = mdl_file
        self.mdl0 = mdl0
        self.flags = flags
        self.image_dir = None
        self.image_library = set()
        self.geometries = []
        self.replacement_model = None
        self.encode = encode
        self.encoder = encoder

    def _start_saving(self, mdl0):
        AutoFix.get().info('Exporting to {}...'.format(self.mdl_file))
        self.start = time.time()
        if mdl0 is None:
            mdl0 = self.mdl0
            if mdl0 is None:
                self.mdl0 = mdl0 = self.brres.models[0]
        else:
            self.mdl0 = mdl0
        self.cwd = os.getcwd()
        work_dir, name = os.path.split(self.mdl_file)
        if work_dir:
            os.chdir(work_dir)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.json_file = base_name + '.json'
        self.influences = decode_mdl0_influences(mdl0)
        self.tex0_map = {}
        return base_name, mdl0

    def _end_saving(self, writer):
        # dump json materials, create image library, write file
        MatsToJsonConverter(self.json_file).export(self.mdl0.materials)
        self.__add_pat0_images()
        self._create_image_library(self.tex0_map.values())
        os.chdir(self.cwd)
        writer.write(self.mdl_file)
        AutoFix.get().info('\t...finished in {} seconds.'.format(round(time.time() - self.start, 2)))

    def _start_loading(self, model_name):
        AutoFix.get().info('Converting {}... '.format(self.mdl_file))
        self.start = time.time()
        self.cwd = os.getcwd()
        self.import_textures_map = {}
        self.mdl_file = os.path.abspath(self.mdl_file)
        library = MaterialLibrary.get()
        self.material_library = library.materials if library else None
        brres_dir, brres_name = os.path.split(self.brres.name)
        base_name = os.path.splitext(brres_name)[0]
        self.is_map = True if 'map' in base_name else False
        work_dir, name = os.path.split(self.mdl_file)
        self.json_file = os.path.join(work_dir, os.path.splitext(name)[0]) + '.json'
        if work_dir:
            os.chdir(work_dir)  # change to the dir to help find relative paths
        return self._init_mdl0(brres_name, os.path.splitext(name)[0], model_name)

    def _before_encoding(self):
        if self.encoder:
            self.encoder.before_encoding(self.geometries)

    def _end_loading(self):
        mdl0 = self.mdl0
        if os.path.exists(self.json_file):
            MatsToJsonConverter(self.json_file).load_into(mdl0.materials)
        import_path_map = self.__normalize_image_path_map(self.import_textures_map)
        self._import_images(import_path_map)
        mdl0.rebuild_header()
        self.brres.add_mdl0(mdl0)
        if self.is_map:
            mdl0.add_map_bones()
        os.chdir(self.cwd)
        AutoFix.get().info('\t... finished in {} secs'.format(round(time.time() - self.start, 2)))
        if self.encoder:
            self.encoder.after_encode(mdl0)
        return mdl0

    def _init_mdl0(self, brres_name, mdl_name, mdl0_name):
        if self.mdl0 is not None:
            self.replacement_model = self.mdl0
            mdl0_name = self.mdl0.name
        else:
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
    def calc_srt_from_bone_matrix(bone):
        tr_matrix = np.array(bone.get_transform_matrix())
        if bone.b_parent:
            inv_matrix = np.array(bone.b_parent.get_inv_transform_matrix())
            tr_matrix = np.around(np.matmul(inv_matrix, tr_matrix), 6)
        # bone.local_transform_matrix = matrix
        return matrix_to_srt(tr_matrix)

    @staticmethod
    def set_bone_matrix(bone, bone_matrix):
        """Untested set translation/scale/rotation with matrix"""
        bone.transform_matrix = bone_matrix[:3]  # don't include fourth row
        bone.inverse_matrix = np.linalg.inv(bone_matrix)[:3]
        scale, rotation, translation = Converter.calc_srt_from_bone_matrix(bone)
        bone.scale = scale
        bone.fixed_scale = np.allclose(scale, 1)
        bone.scale_equal = scale[2] == scale[1] == scale[0]
        bone.rotation = rotation
        bone.fixed_rotation = np.allclose(rotation, 0)
        bone.translation = translation
        bone.fixed_translation = np.allclose(translation, 0)
        bone.no_transform = bone.fixed_scale and bone.fixed_rotation and bone.fixed_translation

    @staticmethod
    def is_identity_matrix(mtx):
        return np.allclose(mtx, matrix.IDENTITY)

    def __add_pat0_images(self):
        """Adds the pat0 images to tex0 library"""
        if self.mdl0.pat0_collection is not None:
            for tex in self.mdl0.pat0_collection.get_used_textures():
                if tex not in self.tex0_map:
                    self.tex0_map[tex] = self.texture_library.get(tex)

    def _encode_material(self, generic_mat):
        m = None
        if self.replacement_model:
            m = self.replacement_model.get_material_by_name(generic_mat.name)
        if m is None:
            if self.material_library:
                m = self.material_library.get(generic_mat)
            if m is None and self.replacement_model:
                m = fuzzy_match(generic_mat.name, self.replacement_model.materials)
        if m is not None:
            mat = material.Material.get_unique_material(generic_mat.name, self.mdl0)
            self.mdl0.add_material(mat)
            mat.paste(m)
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

    def __normalize_image_path_map(self, image_path_map):
        used_tex = self.mdl0.get_used_textures()
        normalized = {}
        for x in image_path_map:
            path = image_path_map[x]
            if self.image_dir is None:
                self.image_dir = os.path.dirname(path)
            tex_name = os.path.splitext(os.path.basename(path))[0]
            if tex_name in used_tex:  # only add it if used
                normalized[tex_name] = path
                used_tex.remove(tex_name)
        for x in used_tex:  # detect any missing that we can find
            path = os.path.join(self.image_dir, x + '.png')
            if os.path.exists(path):
                normalized[x] = path
        return normalized

    def _import_images(self, image_path_map):
        try:
            return self._try_import_textures(self.brres, image_path_map)
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

    def _encode_geometry(self, geometry):
        encoder = self.encoder.get_encoder(geometry) if self.encoder else None
        return geometry.encode(self.mdl0, encoder=encoder)

    def convert(self):
        if self.encode:
            self.load_model()
        else:
            self.save_model()

    def __eq__(self, other):
        return type(self) == type(other) and self.brres is other.brres and self.mdl0 is other.mdl0 \
               and self.mdl_file == other.mdl_file and self.encode == other.encode and self.flags == other.flags \
               and self.encoder == other.encoder

    def load_model(self, model_name=None):
        raise NotImplementedError()

    def save_model(self, mdl0=None):
        raise NotImplementedError()


def float_to_str(fl):
    return ('%f' % fl).rstrip('0').rstrip('.')
