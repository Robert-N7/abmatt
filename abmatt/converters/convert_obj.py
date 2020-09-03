import os
import sys
import time

import numpy as np

from brres import Brres
from brres.mdl0 import Mdl0
from brres.mdl0.material import Material
from brres.tex0 import ImgConverter
from converters.arg_parse import cmdline_convert
from converters.convert_lib import Converter, add_geometry, decode_polygon
from converters.obj import Obj, ObjGeometry, ObjMaterial


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
        dir, name = os.path.split(brres.name)
        base_name = os.path.splitext(name)[0]
        self.is_map = True if 'map' in name else False
        os.chdir(dir)  # change to the collada dir to help find relative paths
        print('Converting {}... '.format(model_file))
        start = time.time()
        if not model_name:
            model_name = base_name.replace('_model', '')
        self.mdl = mdl = Mdl0(model_name, brres)
        bone = mdl.add_bone(base_name)
        obj = Obj(model_file)
        # add images
        for image in obj.images:
            self.try_import_texture(brres, image)

        # add geometries
        for geometry in obj.geometries:
            normals = None if self.NoNormals & self.flags or self.is_map else geometry.normals
            geo = add_geometry(mdl, geometry.name, geometry.vertices, normals, None, [geometry.texcoords])
            mat = obj.materials[geometry.material]
            material = self.encode_material(mat, mdl)
            mdl.add_definition(material, geo, bone)
        mdl.rebuild_header()
        brres.add_mdl0(mdl)
        if self.is_map:
            mdl.add_map_bones()
        os.chdir(cwd)
        print('\t... Finished in {} secs'.format(round(time.time() - start, 2)))
        return mdl

    @staticmethod
    def decode_geometry(geometry, material_name):
        geo = ObjGeometry(geometry['name'])
        geo.material = material_name
        geo.vertices = geometry['vertices']
        geo.normals = geometry['normals']
        texcoords = geometry['texcoords']
        # if len(texcoords) > 1:
        #     print('WARN: Loss of UV data for {}.'.format(geo.name))
        geo.texcoords = texcoords[0]
        geo.triangles = np.stack((geo.vertices.face_indices, geo.texcoords.face_indices, geo.normals.face_indices), -1)
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
        print('INFO: Converting {} to obj...'.format(self.brres.name))
        dir, name = os.path.split(self.mdl_file)
        base_name, ext = os.path.splitext(name)
        self.image_dir = os.path.join(dir, base_name + '_maps')
        self.tex0_map = {}
        self.brres_textures = self.brres.get_texture_map()
        if not mdl0:
            mdl0 = self.brres.models[0]
        polygons = mdl0.objects
        obj = Obj(self.mdl_file, False)
        obj_geometries = obj.geometries
        obj_materials = obj.materials
        obj_images = obj.images
        for x in polygons:
            geometry = decode_polygon(x)
            material = geometry['material']
            obj_materials[material.name] = self.decode_material(material)
            obj_geometries.append(self.decode_geometry(geometry, material.name))
        tex0_map = self.tex0_map
        if len(tex0_map):
            if not os.path.exists(self.image_dir):
                os.mkdir(self.image_dir)
            for tex in tex0_map:
                tex0 = tex0_map[tex]
                destination = os.path.join(self.image_dir, tex + '.png')
                obj_images.add(destination)
                ImgConverter().decode(tex0, destination)
        obj.save()
        print('INFO: Wrote file {}.'.format(obj.filename))

def main():
    cmdline_convert(sys.argv[1:], '.obj', ObjConverter)


if __name__ == '__main__':
    main()
