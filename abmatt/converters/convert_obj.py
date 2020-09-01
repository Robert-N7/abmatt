import os
import sys
import time

from brres import Brres
from brres.mdl0 import Mdl0
from brres.mdl0.material import Material
from converters.arg_parse import cmdline_convert
from converters.convert_lib import Converter, add_geometry
from converters.obj import Obj


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

    def save_model(self, mdl0):
        raise NotImplementedError()


def main():
    cmdline_convert(sys.argv[1:], '.obj', ObjConverter)


if __name__ == '__main__':
    main()
