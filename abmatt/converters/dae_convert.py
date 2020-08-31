import os
import sys
import time

import numpy as np
from collada import Collada, DaeBrokenRefError, DaeUnsupportedError, DaeIncompleteError
from collada.scene import ControllerNode, GeometryNode

from brres import Brres
from brres.mdl0 import Mdl0
from brres.mdl0.material import Material
from brres.tex0 import EncodeError
from converters.convert_lib import add_geometry, PointCollection, ColorCollection, Converter
from converters.arg_parse import arg_parse, cmdline_convert


class DaeConverter(Converter):
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
        m = Material.get_unique_material(dae_material.name, mdl)
        mdl.add_material(m)
        effect = dae_material.effect
        if effect.double_sided:
            m.cullmode = 0
        if effect.transparency > 0:
            m.enable_blend()
        # maps
        DaeConverter.convert_map_to_layer(effect.diffuse, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.ambient, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.specular, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.reflective, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.bumpmap, m, image_path_map)
        DaeConverter.convert_map_to_layer(effect.transparent, m, image_path_map)
        return m

    def encode_geometry(self, geometry, bone):
        mdl = self.mdl
        name = geometry.id
        if not name:
            name = geometry.original.id
        # if not np.allclose(geometry.matrix, self.IDENTITY_MATRIX):
        #     bone = mdl.add_bone(name, bone)
        #     set_bone_matrix(bone, geometry.matrix)

        for triset in geometry.primitives:
            # triset.index[:,[0, 1]] = triset.index[:,[1, 0]]
            vertex_group = PointCollection(triset.vertex, triset.vertex_index)
            if self.flags & self.NoNormals or triset.normal is None:
                normal_group = None
            else:
                normal_group = PointCollection(triset.normal, triset.normal_index)
            tex_coords = []
            for i in range(len(triset.texcoordset)):
                tex_set = triset.texcoordset[i]
                tex_coords.append(PointCollection(tex_set, triset.texcoord_indexset[i]))
            if self.flags & self.NoColors:
                colors = None
            else:
                colors = triset.sources.get('COLOR')
                if colors:
                    color_source = colors[0]
                    face_indices = triset.index[:, :, color_source[0]]
                    colors = ColorCollection(color_source[4].data[:np.max(face_indices) + 1], face_indices)
                    colors.normalize()
            poly = add_geometry(mdl, name, vertex_group, normal_group,
                                colors, tex_coords)
            name = triset.material
            mat = self.materials.get(name)
            if not mat:
                material = Material.get_unique_material(name, mdl)
                mdl.add_material(material)
                if name in self.image_path_map:
                    material.addLayer(name)
            else:
                material = self.encode_material(mat, mdl, self.image_path_map)
            mdl.add_definition(material, poly, bone)
            if colors:
                material.enable_vertex_color()
            break

    @staticmethod
    def get_geometry_by_id(geometries, id):
        geo = geometries[id]
        for x in geometries:
            if x.id == id:
                return x

    def load_model(self, model_name=None):
        brres = self.brres
        model_file = self.mdl_file
        cwd = os.getcwd()
        dir, name = os.path.split(brres.name)
        base_name = os.path.splitext(name)[0]
        os.chdir(dir)   # change to the collada dir to help find relative paths
        print('Converting {}... '.format(self.mdl_file))
        start = time.time()
        dae = Collada(model_file, ignore=[DaeIncompleteError, DaeUnsupportedError, DaeBrokenRefError])
        if not model_name:
            model_name = base_name.replace('_model', '')
        self.mdl = mdl = Mdl0(model_name, brres)
        bone = parent_bone = None
        # images
        self.image_path_map = image_path_map = {}
        for image in dae.images:
            image_path_map[image.path] = self.try_import_texture(brres, image.path)
        if not brres.textures:
            print('ERROR: No textures found!')
        self.materials = dae.materials
        # geometry
        # for node in dae.scene.nodes:
        nodes = dae.scene.nodes
        geometries = dae.geometries
        for node in nodes:
            if len(node.children) < 2:
                geo = geometries.get(node.id)
                if geo and not bone:
                    parent_bone = bone = mdl.add_bone(node.id, parent_bone)
            else:
                if not bone:
                    parent_bone = bone = mdl.add_bone(node.id, parent_bone)
                child = node.children[0]
                t = type(child)
                if t == ControllerNode:
                    geo = child.controller.geometry
                elif t == GeometryNode:
                    geo = child.geometry
                else:
                    geo = None
                if not self.is_identity_matrix(node.matrix):
                    bone = mdl.add_bone(node.id, parent_bone)
                    self.set_bone_matrix(bone, node.matrix)
            if geo:
                self.encode_geometry(geo, bone)
            else:
                bone = mdl.add_bone(node.id, parent_bone)
                if not self.is_identity_matrix(node.matrix):
                    self.set_bone_matrix(bone, node.matrix)
                if not parent_bone:
                    parent_bone = bone

        # for geometry in dae.scene.objects('geometry'):
        #     self.encode_geometry(geometry, bone)
        # for controller in dae.scene.objects('controller'):
        #     self.encode_geometry(controller.geometry, bone)
        mdl.rebuild_header()
        # add model to brres
        brres.add_mdl0(mdl)
        os.chdir(cwd)
        print('\t... Finished in {} secs'.format(round(time.time() - start, 2)))
        return mdl

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


if __name__ == '__main__':
    cmdline_convert(sys.argv[1:], '.dae', DaeConverter)
