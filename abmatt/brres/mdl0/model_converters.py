import math
import os

from collada import Collada, DaeBrokenRefError, DaeUnsupportedError

from brres.mdl0 import Mdl0
from brres.mdl0.color import ColorCollection
from brres.mdl0.geometry import PointCollection
from brres.mdl0.layer import Layer
from brres.mdl0.material import Material
from brres.tex0 import ImgConverter


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

    def convert_map_to_layer(self, map, material):
        if not map or isinstance(map, tuple):
            return
        sampler = map.sampler
        image_path = sampler.surface.image.path
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        # try to add texture?
        if not self.brres.hasTexture(base_name):
            self.brres.import_texture(image_path)
        # create the layer
        l = material.addLayer(base_name)
        if sampler.minfilter:
            pass    # todo update layer minfilter
        coord = 'texcoord' + map.texcoord[-1]
        l.setCoordinateStr(coord)

    def encode_material(self, dae_material, mdl):
        m = Material(dae_material.name, mdl)
        mdl.add_material(m)
        effect = dae_material.effect
        if effect.double_sided:
            m.cullmode = 0
        if effect.transparency < 1:
            m.enable_blend()
        # maps
        self.convert_map_to_layer(effect.diffuse, m)
        self.convert_map_to_layer(effect.ambient, m)
        self.convert_map_to_layer(effect.specular, m)
        self.convert_map_to_layer(effect.reflective, m)
        self.convert_map_to_layer(effect.bumpmap, m)
        self.convert_map_to_layer(effect.transparent, m)

    def load_model(self, model_name=None):
        brres = self.brres
        model_file = self.mdl_file
        base_name = os.path.splitext(os.path.basename(brres))[0]
        dae = Collada(model_file, ignore=[DaeUnsupportedError, DaeBrokenRefError])
        mdl_name = base_name.replace('_model', '')
        mdl = Mdl0(mdl_name, brres)
        bone = mdl.add_bone(base_name)
        # materials
        for material in dae.materials:
            self.encode_material(material, mdl)

        # geometry/vertices/colors
        for geometry in dae.geometries:
            triset = geometry.primitives[0]
            vertex_group = PointCollection(triset.vertex, triset.vertex_index)
            normal_group = PointCollection(triset.normal, triset.normal_index)
            tex_coords = [PointCollection(triset.texcoordset[i], triset.texcoord_indexset[i]) \
                          for i in range(len(triset.texcoordset))]
            if triset.sources.get('COLOR'):
                color_source = triset.sources['COLOR'][0]
                colors = ColorCollection(color_source[4].data, triset.index[:, :, color_source[0]])
            else:
                colors = None
            poly = mdl.add_geometry(base_name, vertex_group, normal_group,
                             colors, tex_coords)
            mdl.add_definition(mdl.getMaterialByName(triset.material), poly, bone)

        # add model to brres
        brres.add_mdl0(mdl)

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

    def save_model(self, mdl0):
        pass
