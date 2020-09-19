import os
import sys
import time

import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.mdl0.material import Material
from abmatt.brres.tex0 import ImgConverter, NoImgConverterError
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Converter, add_geometry, decode_polygon
from abmatt.converters.obj import Obj, ObjGeometry, ObjMaterial


class ObjConverter(Converter):

    @staticmethod
    def convert_map_to_layer(material, map):
        base_name = os.path.splitext(os.path.basename(map))[0]
        if not material.getLayerByName(base_name):
            return material.addLayer(base_name)

    def encode_material(self, obj_mat, mdl):
        material = Material.get_unique_material(obj_mat.name, mdl)
        mdl.add_material(material)
        if obj_mat.dissolve < 1:
            material.enable_blend()
        for x in obj_mat.get_maps():
            self.convert_map_to_layer(material, x)
        return material

    def load_model(self, model_name=None):
        # setup
        model_file = self.mdl_file
        brres = self.brres
        cwd = os.getcwd()
        brres_dir, name = os.path.split(brres.name)
        base_name = os.path.splitext(name)[0]
        self.is_map = True if 'map' in base_name else False
        dir, name = os.path.split(model_file)
        if not model_name:
            model_name = self.get_mdl0_name(base_name, name)
        os.chdir(dir)  # change to the collada dir to help find relative paths
        AUTO_FIXER.info('Converting {}... '.format(model_file))
        start = time.time()
        self.mdl = mdl = Mdl0(model_name, brres)
        bone = mdl.add_bone(base_name)
        obj = Obj(name)
        # add images
        try:
            for image in obj.images:
                self.try_import_texture(brres, image)
        except NoImgConverterError as e:
            AUTO_FIXER.error(e)
        # add geometries
        for geometry in obj.geometries:
            normals = None if self.NoNormals & self.flags or self.is_map else geometry.normals
            texcoords = [geometry.texcoords] if geometry.has_texcoords else None
            geo = add_geometry(mdl, geometry.name, geometry.vertices, normals, None, texcoords)
            mat = obj.materials[geometry.material_name]
            material = self.encode_material(mat, mdl)
            mdl.add_definition(material, geo, bone)
        mdl.rebuild_header()
        brres.add_mdl0(mdl)
        if self.is_map:
            mdl.add_map_bones()
        os.chdir(cwd)
        AUTO_FIXER.info('\t... Finished in {} secs'.format(round(time.time() - start, 2)))
        return mdl

    @staticmethod
    def decode_geometry(geometry, material_name):
        geo = ObjGeometry(geometry.name)
        geo.material_name = material_name
        geo.vertices = geometry.vertices
        geo.normals = geometry.normals
        geo.has_normals = bool(geo.normals)
        texcoords = geometry.texcoords
        # if len(texcoords) > 1:
        #     print('WARN: Loss of UV data for {}.'.format(geo.name))
        stack = [geo.vertices.face_indices]
        if len(texcoords):
            geo.texcoords = texcoords[0]
            stack.append(geo.texcoords.face_indices)
            geo.has_texcoords = True
        else:
            geo.texcoords = None
            geo.has_texcoords = False
        if geo.normals:
            stack.append(geo.normals.face_indices)
        geo.triangles = np.stack(stack, -1)
        # if geometry['colors']:
        #     print('WARN: Loss of color data for {}'.format(geo.name))
        return geo

    def decode_material(self, material):
        mat = ObjMaterial(material.name)
        if material.xlu:
            mat.dissolve = 0.5
        first = True
        for layer in material.layers:
            name = layer.name
            if name not in self.tex0_map:
                tex = self.brres_textures.get(name)
                if tex:
                    self.tex0_map[name] = tex
            if first:
                path = os.path.join(self.image_dir, name + '.png')
                mat.diffuse_map = path
                mat.ambient_map = path
            first = False
        return mat

    def save_model(self, mdl0=None):
        AUTO_FIXER.info('Exporting to {}...'.format(self.mdl_file))
        start = time.time()
        dir, name = os.path.split(self.mdl_file)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.tex0_map = {}
        self.brres_textures = self.brres.get_texture_map()
        if not mdl0:
            mdl0 = self.brres.models[0]
        polygons = mdl0.objects
        obj = Obj(self.mdl_file, False)
        obj_materials = obj.materials
        for mat in mdl0.materials:
            obj_mat = self.decode_material(mat)
            obj_materials[obj_mat.name] = obj_mat
        obj_geometries = obj.geometries
        obj_images = obj.images
        for x in polygons:
            geometry = decode_polygon(x)
            material = geometry.material_name
            obj_geometries.append(self.decode_geometry(geometry, material))
        tex0_map = self.tex0_map
        if len(tex0_map):
            converter = ImgConverter()
            if not converter:
                AUTO_FIXER.error('No image converter found!')
            image_dir = os.path.join(dir, self.image_dir)
            if not os.path.exists(image_dir):
                os.mkdir(image_dir)
            tmp = os.getcwd()
            os.chdir(image_dir)
            for tex in tex0_map:
                tex0 = tex0_map[tex]
                destination = os.path.join(tex + '.png')
                obj_images.add(destination)
                if converter:
                    converter.decode(tex0, destination)
            os.chdir(tmp)
        obj.save()
        AUTO_FIXER.info('\t...finished in {} seconds.'.format(round(time.time() - start, 2)))


def main():
    cmdline_convert(sys.argv[1:], '.obj', ObjConverter)


if __name__ == '__main__':
    main()
