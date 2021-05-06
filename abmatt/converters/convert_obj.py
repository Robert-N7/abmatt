import os
import sys

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Converter
from abmatt.converters.geometry import Geometry
from abmatt.converters.material import Material
from abmatt.converters.obj import Obj, ObjGeometry, ObjMaterial


class ObjConverter(Converter):

    def __collect_geometries(self, obj_geometries, bone):
        material_geometry_map = {}
        # first collect geometries
        for geometry in obj_geometries:
            normals = None if self.NO_NORMALS & self.flags else geometry.normals
            texcoords = [geometry.texcoords] if geometry.has_texcoords else None
            geo = Geometry(geometry.name, geometry.material_name, geometry.vertices, texcoords, normals,
                           triangles=geometry.triangles, linked_bone=bone)
            # geo.encode(self.mdl0)
            mat = geometry.material_name
            if mat in material_geometry_map:
                material_geometry_map[mat].combine(geo)
            else:
                material_geometry_map[mat] = geo
                self.geometries.append(geo)
        return material_geometry_map

    def load_model(self, model_name=None):
        mdl = self._start_loading(model_name)
        bone = mdl.add_bone(mdl.name)
        obj = Obj(self.mdl_file)
        material_geometry_map = self.__collect_geometries(obj.geometries, bone)

        self._before_encoding()
        for material in material_geometry_map:
            try:
                self.__encode_material(obj.materials[material])
            except KeyError:
                self._encode_material(Material(material))
            super()._encode_geometry(material_geometry_map[material])
        self.import_textures_map = self.__convert_set_to_map(obj.images)
        return self._end_loading()

    def save_model(self, mdl0=None):
        base_name, mdl0 = self._start_saving(mdl0)
        polygons = mdl0.objects
        obj = Obj(self.mdl_file, False)
        obj_materials = obj.materials
        for mat in mdl0.materials:
            obj_mat = self.__decode_material(mat)
            obj_materials[obj_mat.name] = obj_mat
        obj_geometries = obj.geometries
        for x in polygons:
            geometry = x.get_decoded()
            material = geometry.material_name
            obj_geometries.append(self.__decode_geometry(geometry, material))
        self._end_saving(obj)

    @staticmethod
    def __convert_map_to_layer(material, map):
        base_name = os.path.splitext(os.path.basename(map))[0]
        if not material.getLayerByName(base_name):
            return material.add_layer(base_name)

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
        if geometry.colors:
            AutoFix.get().warn('Loss of color data for {}'.format(geo.name))
        texcoords = geometry.texcoords
        if len(texcoords) > 1:
            AutoFix.get().warn('Loss of UV data for {}.'.format(geo.name))
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
                tex = self.texture_library.get(name)
                if tex:
                    self.tex0_map[name] = tex
                else:
                    AutoFix.get().warn('No texture found matching {}'.format(name))
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
