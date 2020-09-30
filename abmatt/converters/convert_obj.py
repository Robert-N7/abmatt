import os
import sys
import time

import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.tex0 import ImgConverter
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Converter, add_geometry
from converters.material import Material
from converters.geometry import Geometry, decode_polygon
from abmatt.converters.obj import Obj, ObjGeometry, ObjMaterial


class ObjConverter(Converter):

    def __collect_geometries(self, obj_geometries, bone):
        material_geometry_map = {}
        # first collect geometries
        for geometry in obj_geometries:
            normals = None if self.NoNormals & self.flags or self.is_map else geometry.normals
            texcoords = [geometry.texcoords] if geometry.has_texcoords else None
            geo = Geometry(geometry.name, geometry.material_name, geometry.vertices, texcoords, normals,
                           triangles=geometry.triangles, linked_bone=bone)
            # geo.encode(self.mdl0)
            mat = geometry.material_name
            if mat in material_geometry_map:
                material_geometry_map[mat].combine(geometry)
            else:
                material_geometry_map[mat] = geo
        return material_geometry_map

    def load_model(self, model_name=None):
        mdl = self._start_loading(model_name)
        bone = mdl.add_bone(mdl.name)
        obj = Obj(self.mdl_file)
        material_geometry_map = self.__collect_geometries(obj.geometries, bone)
        for material in material_geometry_map:
            self.__encode_material(obj.materials[material])
            material_geometry_map[material].encode(mdl)
        self._import_images(self.__convert_set_to_map(obj.images))
        return self._end_loading()

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
            obj_mat = self.__decode_material(mat)
            obj_materials[obj_mat.name] = obj_mat
        obj_geometries = obj.geometries
        obj_images = obj.images
        for x in polygons:
            geometry = decode_polygon(x)
            material = geometry.material_name
            obj_geometries.append(self.__decode_geometry(geometry, material))
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

    @staticmethod
    def __convert_map_to_layer(material, map):
        base_name = os.path.splitext(os.path.basename(map))[0]
        if not material.getLayerByName(base_name):
            return material.addLayer(base_name)

    def __convert_set_to_map(self, obj_images):
        path_map = {}
        for x in obj_images:
            path_map[os.path.splitext(os.path.basename(x))[0]] = x
        return path_map

    def __encode_material(self, obj_mat):
        return self._encode_material(Material(obj_mat.name, obj_mat.diffuse_map, obj_mat.ambient_map,
                                              obj_mat.specular_map, obj_mat.get_transparency()))

    @staticmethod
    def __decode_geometry(geometry, material_name):
        geo = ObjGeometry(geometry.name)
        geo.vertices = geometry.apply_linked_bone_bindings()
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
        return geo

    def __decode_material(self, material):
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


def main():
    cmdline_convert(sys.argv[1:], '.obj', ObjConverter)


if __name__ == '__main__':
    main()
