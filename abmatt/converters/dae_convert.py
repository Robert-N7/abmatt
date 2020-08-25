import os
import sys
import time

from collada import Collada, DaeBrokenRefError, DaeUnsupportedError, DaeIncompleteError

from brres import Brres
from brres.mdl0 import Mdl0
from brres.mdl0.material import Material
from brres.tex0 import EncodeError
from converters.convert_lib import add_geometry, PointCollection, ColorCollection


class Converter:
    def __init__(self, brres, mdl_file):
        self.brres = brres
        self.mdl_file = mdl_file

    @staticmethod
    def set_image_format(frmt):
        Converter.IMG_DEFAULT_FORMAT = frmt

    def load_model(self, model_name):
        raise NotImplementedError()

    def save_model(self, mdl0):
        raise NotImplementedError()


class DaeConverter(Converter):
    @staticmethod
    def try_import_texture(brres, image_path):
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        if not brres.hasTexture(base_name):
            try:
                brres.import_texture(image_path)
            except EncodeError:
                pass
        return base_name

    @staticmethod
    def convert_map_to_layer(map, material, image_path_map):
        if not map or isinstance(map, tuple):
            return
        sampler = map.sampler
        base_name = image_path_map[sampler.surface.image.path]
        # create the layer
        if not material.getLayerByName(base_name):
            l = material.addLayer(base_name)
            if sampler.minfilter:
                pass  # todo update layer minfilter
            coord = 'texcoord' + map.texcoord[-1]
            l.setCoordinatesStr(coord)

    @staticmethod
    def encode_material(dae_material, mdl, image_path_map):
        m = Material(dae_material.name, mdl)
        mdl.add_material(m)
        effect = dae_material.effect
        if effect.double_sided:
            m.cullmode = 0
        if effect.transparency < 1:
            m.enable_blend()
        # maps
        DaeConverter.convert_map_to_layer(effect.diffuse, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.ambient, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.specular, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.reflective, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.bumpmap, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.transparent, m, image_path_map)

    def load_model(self, model_name=None):
        start = time.time()
        print('Converting {}... '.format(self.mdl_file))
        brres = self.brres
        model_file = self.mdl_file
        base_name = os.path.splitext(os.path.basename(brres.name))[0]
        dae = Collada(model_file, ignore=[DaeIncompleteError, DaeUnsupportedError, DaeBrokenRefError])
        mdl_name = base_name.replace('_model', '')
        mdl = Mdl0(mdl_name, brres)
        bone = mdl.add_bone(base_name)
        # images
        image_path_map = {}
        for image in dae.images:
            image_path_map[image.path] = self.try_import_texture(brres, image.path)
        # materials
        for material in dae.materials:
            self.encode_material(material, mdl, image_path_map)
        if not brres.textures:
            print('ERROR: No textures found!')
        # geometry/vertices/colors
        for geometry in dae.geometries:
            triset = geometry.primitives[0]
            vertex_group = PointCollection(triset.vertex, triset.vertex_index)
            normal_group = PointCollection(triset.normal, triset.normal_index) if triset.normal is not None else None
            tex_coords = [PointCollection(triset.texcoordset[i], triset.texcoord_indexset[i]) \
                          for i in range(len(triset.texcoordset))]
            if triset.sources.get('COLOR'):
                color_source = triset.sources['COLOR'][0]
                colors = ColorCollection(color_source[4].data, triset.index[:, :, color_source[0]])
                colors.normalize()
            else:
                colors = None
            poly = add_geometry(mdl, geometry.name.rstrip('Mesh'), vertex_group, normal_group,
                                colors, tex_coords)
            material = mdl.getMaterialByName(triset.material)
            if not material:    # broken material
                material = mdl.add_material(Material(triset.material, mdl))
                material.auto_detect_layer()
            mdl.add_definition(material, poly, bone)
            if colors:
                material.enable_vertex_color()
        mdl.rebuild_header()
        # add model to brres
        brres.add_mdl0(mdl)
        print('\t... Finished in {}'.format(time.time() - start))

    @staticmethod
    def convert_colors(color_group):
        return color_group


    @staticmethod
    def construct_indices(triset_group, stride=3):
        geo_group = []
        ln = 0
        indices = []
        b = stride
        c = b + stride
        maximum = triset_group[0][:b]
        minimum = [x for x in maximum]
        for x in triset_group:
            points = [x[:b], x[b:c], x[c:]]
            for point in points:
                found = False
                for i in range(ln):
                    if point == geo_group[i]:
                        indices.append(i)
                        found = True
                        break
                if not found:
                    geo_group.append(point)
                    for i in range(3):
                        if point[i] < minimum[i]:
                            minimum[i] = point[i]
                        elif point[i] > maximum[i]:
                            maximum[i] = point[i]
                    indices.append(ln)
                    ln += 1
        return PointCollection(geo_group, indices, minimum, maximum)

    def save_model(self, mdl0=None):
        raise NotImplementedError()


def main(args):
    from converters.arg_parse import arg_parse
    file_in, file_out, overwrite = arg_parse(args)
    if file_in.ext == '.brres':
        if not file_out.ext:
            file_out.ext = '.dae'
        brres = Brres(file_in.get_path())
        converter = DaeConverter(brres, file_out.get_path())
        converter.save_model()
    elif file_in.ext.lower() == '.dae':
        b_path = file_out.get_path()
        brres = Brres(b_path, None, os.path.exists(b_path))
        converter = DaeConverter(brres, file_in.get_path())
        converter.load_model()
        brres.save(None, overwrite)
    else:
        print('Unknown file {}, is the file extension .dae?'.format(file_in.ext))
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
