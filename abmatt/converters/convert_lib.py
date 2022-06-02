import os
import time

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.converters.error import ConvertError
from abmatt.brres.lib.matching import fuzzy_match
from abmatt.brres.material_library import MaterialLibrary
from abmatt.brres.mdl0.material import material
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.command import Command
from abmatt.converters import matrix
from abmatt.converters.convert_mats_to_json import MatsToJsonConverter
from abmatt.converters.matrix import matrix_to_srt
from abmatt.image_converter import EncodeError, NoImgConverterError, ImgConverter
from abmatt.converters import influence


class Converter:
    NO_NORMALS = 0x1
    NO_COLORS = 0x2
    SINGLE_BONE = 0x4
    NO_UVS = 0x8
    PATCH = 0x10
    MOONVIEW = 0x20
    DETECT_FILE_UNITS = True
    OVERWRITE_IMAGES = False
    ENCODE_PRESET = None
    ENCODE_PRESET_ON_NEW = True

    def __init__(self, brres, mdl_file, flags=0, encode=True, mdl0=None, encoder=None,
                 include=None, exclude=None):
        if not brres:
            # filename = Brres.getExpectedBrresFileName(mdl_file)
            d, f = os.path.split(mdl_file)
            filename = os.path.join(d, os.path.splitext(f)[0] + '.brres')
            brres = Brres.get_brres(filename, True)
        elif type(brres) == str:
            brres = Brres.get_brres(brres, True)
        self.brres = brres
        self.include = include
        self.exclude = exclude
        self.patch_existing = False
        self.texture_library = brres.get_texture_map()
        self.mdl_file = mdl_file
        self.mdl0 = mdl0 if type(mdl0) == Mdl0 else brres.get_model(mdl0)
        self.flags = flags
        self.image_dir = None
        self.replacement_model = None
        self.encode = encode
        self.encoder = encoder

    def _start_saving(self, mdl0):
        AutoFix.info('Exporting {} to {}...'.format(os.path.basename(self.brres.name), self.mdl_file))
        self.start = time.time()
        self.image_library = set()
        if mdl0 is None:
            mdl0 = self.mdl0
            if mdl0 is None:
                self.mdl0 = mdl0 = self.brres.models[0]
        else:
            self.mdl0 = mdl0
        if type(mdl0) == str:
            self.mdl0 = mdl0 = self.brres.get_model(mdl0)
        if mdl0 is None:
            raise RuntimeError('No mdl0 file found to export!')
        self.polygons = [x for x in mdl0.objects if self._should_include_geometry(x)]
        mats = []
        for x in self.polygons:
            if x.material not in mats:
                mats.append(x.material)
        self.materials = mats
        self.cwd = os.getcwd()
        work_dir, name = os.path.split(self.mdl_file)
        if work_dir:
            os.chdir(work_dir)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.json_file = base_name + '.json'
        self.influences = mdl0.get_influences()
        self.bones = {}
        self.tex0_map = {}
        return base_name, mdl0

    def _end_saving(self, writer):
        # dump json materials, create image library, write file
        MatsToJsonConverter(self.json_file).export(self.mdl0.materials)
        self.__add_pat0_images()
        self._create_image_library(self.tex0_map.values())
        os.chdir(self.cwd)
        writer.write(self.mdl_file)
        AutoFix.info('\t...finished in {} seconds.'.format(round(time.time() - self.start, 2)))
        return self.mdl_file

    def _start_loading(self, model_name):
        AutoFix.info('Converting {}... '.format(self.mdl_file))
        self.start = time.time()
        self.image_library = set()
        self.geometries = []
        self.cwd = os.getcwd()
        self.import_textures_map = {}
        self.mdl_file = os.path.abspath(self.mdl_file)
        library = MaterialLibrary.get()
        self.material_library = library.materials if library else None
        brres_dir, brres_name = os.path.split(self.brres.name)
        base_name = os.path.splitext(brres_name)[0]
        mdl_file_base_name = os.path.splitext(os.path.basename(self.mdl_file))[0]
        self.is_map = True if 'map' in base_name or mdl_file_base_name == 'map_model' else False
        work_dir, name = os.path.split(self.mdl_file)
        self.json_file = os.path.join(work_dir, os.path.splitext(name)[0]) + '.json'
        if work_dir:
            os.chdir(work_dir)  # change to the dir to help find relative paths
        return self._init_mdl0(brres_name, os.path.splitext(name)[0], model_name)

    def _before_encoding(self):
        if not self.geometries:
            raise ConvertError('No geometries found to encode!')
        self.removed_materials = {}
        if self.patch_existing:
            replace_names = [x.name for x in self.geometries]
            for poly in [x for x in self.replacement_model.objects if x.name in replace_names]:
                self.removed_materials[poly.material.name] = poly.material
                self.replacement_model.remove_polygon(poly)
        self.material_name_remap = material_name_remap = {}
        self.encode_materials()
        for x in self.geometries:
            if x.material_name in material_name_remap:
                x.material_name = material_name_remap[x.material_name]

        if os.path.exists(self.json_file):
            converter = MatsToJsonConverter(self.json_file)
            converter.load_into(self.mdl0.materials, material_name_remap)
            self.json_polygon_encoding = converter.polygons_by_name
        else:
            self.json_polygon_encoding = None
        if self.encoder:
            self.encoder.before_encoding(self)

    def _end_loading(self):
        mdl0 = self.mdl0
        import_path_map = self.__normalize_image_path_map(self.import_textures_map)
        self._import_images(import_path_map)
        mdl0.rebuild_header()
        self.brres.add_mdl0(mdl0)
        if self.is_map:
            mdl0.add_map_bones()
        os.chdir(self.cwd)
        if self.ENCODE_PRESET:
            if not self.ENCODE_PRESET_ON_NEW or (self.replacement_model is None and self.json_polygon_encoding is None):
                Command(
                    'preset ' + self.ENCODE_PRESET + ' for * in ' + self.brres.name + ' model ' + self.mdl0.name).run_cmd()
        AutoFix.info('\t... finished in {} secs'.format(round(time.time() - self.start, 2)))
        if self.encoder:
            self.encoder.after_encode(mdl0)
        if self.MOONVIEW & self.flags:
            self.brres.check_moonview()
        return mdl0

    def _init_mdl0(self, brres_name, mdl_name, mdl0_name):
        if self.mdl0 is not None:
            self.replacement_model = self.mdl0
            mdl0_name = self.mdl0.name
        else:
            if mdl0_name is None:
                mdl0_name = self.__get_mdl0_name(brres_name, mdl_name)
            self.replacement_model = self.mdl0 = self.brres.get_model(mdl0_name)
        if self.flags & self.PATCH and self.replacement_model:
            self.patch_existing = True
            if any(x.has_weights() for x in self.replacement_model.objects):
                raise RuntimeError('Patching rigged models is not supported!')
        if not self.patch_existing or not self.replacement_model:
            self.mdl0 = Mdl0(mdl0_name, self.brres)
        return self.mdl0

    def _should_include_geometry(self, geometry):
        if self.include:
            return geometry.name in self.include
        elif self.exclude:
            return geometry.name not in self.exclude
        return True

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
        for material in self.mdl0.materials:
            if material.pat0:
                for tex in material.pat0.get_used_textures():
                    if tex not in self.tex0_map:
                        self.tex0_map[tex] = self.texture_library.get(tex)

    def _encode_material(self, generic_mat):
        m = None
        if self.replacement_model:
            m = self.removed_materials.get(generic_mat.name)
            if m is None:
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
        if mat.name != generic_mat.name:
            self.material_name_remap[generic_mat.name] = mat.name
        for x in mat.layers:
            self.image_library.add(x.name)
        return mat

    def _create_image_library(self, tex0s):
        if not tex0s:
            return True
        converter = ImgConverter()
        if not converter:
            AutoFix.error('No image converter found!')
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
        if self.image_dir is not None:
            for x in used_tex:  # detect any missing that we can find
                path = os.path.join(self.image_dir, x + '.png')
                if os.path.exists(path):
                    normalized[x] = path
        return normalized

    def _import_images(self, image_path_map):
        try:
            return self._try_import_textures(self.brres, image_path_map)
        except NoImgConverterError as e:
            AutoFix.exception(e)

    @staticmethod
    def _try_import_textures(brres, image_paths):
        if len(image_paths):
            try:
                converter = ImgConverter()
                converter.batch_encode(image_paths.values(), brres, overwrite=converter.OVERWRITE_IMAGES)
            except EncodeError:
                AutoFix.warn('Failed to encode images')
        return image_paths

    def __get_single_bone_influence(self):
        bone = list(self.bones.values())[0] if len(self.bones) else self.mdl0.bones[0]
        return influence.InfluenceCollection({0: influence.Influence(
            bone_weights={bone.name: influence.Weight(bone, 1.0)})})

    def _decode_geometry(self, polygon):
        if not self._should_include_geometry(polygon):
            return
        geo = polygon.get_decoded()
        if geo.colors and self.flags & self.NO_COLORS:
            geo.colors = None
        if geo.normals and self.flags & self.NO_NORMALS:
            geo.normals = None
        if self.flags & self.SINGLE_BONE:
            geo.influences = self.__get_single_bone_influence()
        if self.flags & self.NO_UVS:
            geo.texcoords = []
        return geo

    def _encode_geometry(self, geometry):
        if not self._should_include_geometry(geometry):
            return
        if self.flags & self.NO_COLORS:
            geometry.colors = None
        if self.flags & self.NO_NORMALS:
            geometry.normals = None
        if self.flags & self.NO_UVS:
            geometry.texcoords = []
        has_uv_mtx = priority = None
        json_data = self.json_polygon_encoding.get(geometry.name) if self.json_polygon_encoding else None
        if json_data:
            has_uv_mtx = json_data.get('has_uv_matrix')
            priority = json_data.get('draw_priority')
        elif self.replacement_model:
            for x in self.replacement_model.objects:
                if x.name == geometry.name:
                    has_uv_mtx = [x.has_uv_matrix(i) for i in range(8)]
                    priority = x.priority
                    if self.patch_existing:
                        self.mdl0.remove_polygon(x)
                    break
        encoder = self.encoder.get_encoder(geometry) if self.encoder else None
        return geometry.encode(self.mdl0, encoder=encoder,
                               priority=priority,
                               has_uv_mtx=has_uv_mtx)

    def convert(self):
        if self.encode:
            self.load_model()
        else:
            self.save_model()
        return self

    def __eq__(self, other):
        return type(self) == type(other) and self.brres is other.brres and self.mdl0 is other.mdl0 \
               and self.mdl_file == other.mdl_file and self.encode == other.encode and self.flags == other.flags \
               and self.encoder == other.encoder

    def load_model(self, model_name=None):
        raise NotImplementedError()

    def save_model(self, mdl0=None):
        raise NotImplementedError()

    def encode_materials(self):
        raise NotImplementedError()


def float_to_str(fl):
    return ('%f' % fl).rstrip('0').rstrip('.')
