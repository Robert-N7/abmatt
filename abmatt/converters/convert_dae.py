import os
import sys
import time

import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.tex0 import ImgConverter, NoImgConverterError
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Controller
from abmatt.converters.convert_lib import Converter, decode_polygon, \
    Material, combine_matrices
from abmatt.converters.dae import Dae, ColladaNode


class DaeConverter2(Converter):

    def load_model(self, model_name=None):
        self._start_loading(model_name)
        self.bones = {}
        self.dae = dae = Dae(self.mdl_file)
        self.__parse_materials(dae.get_materials())
        # geometry
        matrix = np.identity(4)
        if self.DETECT_FILE_UNITS:
            if dae.unit_meter != 1:     # set the matrix scale to convert to meters
                for i in range(3):
                    matrix[i][i] = dae.unit_meter
        material_geometry_map = {}
        self.__parse_nodes(dae.get_scene(), material_geometry_map, matrix)
        for material in material_geometry_map:
            geometries = material_geometry_map[material]
            for x in geometries:
                self.__encode_geometry(x)
        self._import_images(dae.get_images())
        return self._end_loading()

    def save_model(self, mdl0=None):
        AUTO_FIXER.info('Exporting to {}...'.format(self.mdl_file))
        start = time.time()
        if not mdl0:
            mdl0 = self.brres.models[0]
        cwd = os.getcwd()
        dir, name = os.path.split(self.mdl_file)
        if dir:
            os.chdir(dir)
        base_name, ext = os.path.splitext(name)
        self.image_dir = base_name + '_maps'
        self.texture_library = self.brres.get_texture_map()
        self.tex0_map = {}
        mesh = Dae(initial_scene_name=base_name)
        decoded_mats = [self.__decode_material(x) for x in mdl0.materials]
        # images
        self.__create_image_library(mesh)
        # polygons
        polygons = mdl0.objects
        mesh.add_node(self.__decode_bone(mdl0.bones[0]))
        for polygon in polygons:
            mesh.add_node(self.__decode_geometry(polygon))
        for mat in decoded_mats:
            mesh.add_material(mat)
        os.chdir(cwd)
        mesh.write(self.mdl_file)
        AUTO_FIXER.info('\t...finished in {} seconds.'.format(round(time.time() - start, 2)))

    def __decode_bone(self, mdl0_bone, collada_parent=None):
        name = mdl0_bone.name
        node = ColladaNode(name, {'type': 'JOINT'})
        node.matrix = np.array(mdl0_bone.get_transform_matrix())
        if collada_parent:
            collada_parent.nodes.append(node)
        if mdl0_bone.child:
            self.__decode_bone(mdl0_bone.child, node)
        if mdl0_bone.next:
            self.__decode_bone(mdl0_bone.next, collada_parent)
        return node

    def __decode_geometry(self, polygon):
        name = polygon.name
        node = ColladaNode(name)
        geo = decode_polygon(polygon)
        if geo.colors and self.flags & self.NoColors:
            geo.colors = None
        if geo.normals and self.flags & self.NoNormals:
            geo.normals = None
        node.geometries.append(geo)
        node.controller = get_controller(geo)
        return node

    def __decode_material(self, material):
        diffuse_map = ambient_map = specular_map = None
        for i in range(len(material.layers)):
            layer = material.layers[i].name
            if i == 0:
                diffuse_map = layer
            elif i == 1:
                ambient_map = layer
            elif i == 2:
                specular_map = layer
            if layer not in self.tex0_map:
                tex0 = self.texture_library.get(layer)
                map_path = os.path.join(self.image_dir, layer + '.png')
                self.tex0_map[layer] = (tex0, map_path)
        return Material(material.name, diffuse_map, ambient_map, specular_map, material.xlu * 0.5)

    def __create_image_library(self, mesh):
        if len(self.tex0_map):
            converter = ImgConverter()
            if not converter:
                AUTO_FIXER.error('No image converter found!')
            if not os.path.exists(self.image_dir):
                os.mkdir(self.image_dir)
            os.chdir(self.image_dir)
            for image_name in self.tex0_map:
                tex, path = self.tex0_map[image_name]
                mesh.add_image(image_name, path)
                if not tex:
                    AUTO_FIXER.warn('Missing texture {}'.format(image_name))
                    continue
                if converter:
                    converter.decode(tex, image_name + '.png')

    def __parse_controller(self, controller, matrix, material_geometry_map):
        bones = controller.bones
        if len(bones) > 1:
            AUTO_FIXER.warn('Rigged Models not supported!')
        bone = self.bones[bones[0]]
        geometry = controller.get_bound_geometry(matrix)
        geometry.linked_bone = bone
        self.__add_geometry(geometry, material_geometry_map)

    def __encode_geometry(self, geometry, bone=None):
        if not self.dae.y_up:
            geometry.swap_y_z_axis()
        if self.flags & self.NoColors:
            geometry.colors = None
        if self.flags & self.NoNormals:
            geometry.normals = None
        replace = 'Mesh'
        if geometry.name.endswith(replace) and len(replace) < len(geometry.name):
            geometry.name = geometry.name[:len(replace) * -1]
        geometry.encode(self.mdl0, bone)

    def __add_bone(self, node, parent_bone=None, matrix=None):
        name = node.attributes['id']
        self.bones[name] = bone = self.mdl0.add_bone(name, parent_bone)
        self.set_bone_matrix(bone, matrix)
        for n in node.nodes:
            self.__add_bone(n, bone, matrix=n.get_matrix())

    def __add_geometry(self, geometry, material_geometry_map):
        geo = material_geometry_map.get(geometry.material_name)
        add_geo = True
        if geo is not None:
            if not geo[0].combine(geometry):
                geo.append(geometry)
        else:
            material_geometry_map[geometry.material_name] = [geometry]

    def __parse_nodes(self, nodes, material_geometry_map, matrix=None):
        for node in nodes:
            current_node_matrix = combine_matrices(matrix, node.matrix)
            bone_added = False
            if node.controller:
                self.__parse_controller(node.controller, current_node_matrix, material_geometry_map)
            elif node.geometries:
                for x in node.geometries:
                    if current_node_matrix is not None:
                        x.apply_matrix(current_node_matrix)
                    self.__add_geometry(x, material_geometry_map)
                    # self.__encode_geometry(x)
            elif node.attributes.get('type') == 'JOINT':
                self.__add_bone(node, matrix=current_node_matrix)
                bone_added = True
            if not bone_added:
                self.__parse_nodes(node.nodes, {}, current_node_matrix)

    def __parse_materials(self, materials):
        for material in materials:
            self._encode_material(material)


def get_controller(geometry):
    vert_len = len(geometry.vertices)
    bones = geometry.bones
    bone_names = [x.name for x in bones]
    inv_bind_matrix = np.array([x.get_inv_transform_matrix() for x in bones], np.float)
    bind_matrix = np.array(geometry.linked_bone.get_transform_matrix(), np.float)
    # inv_bind_matrix = np.linalg.inv(bind_matrix)
    weights = np.array([1])
    if geometry.bone_indices is None:
        weight_indices = np.full((vert_len, 2), 0, np.uint)
    else:
        weight_indices = np.stack([geometry.bone_indices, np.full(geometry.bone_indices.shape, 0, np.uint)], -1)
    # weight_indices = np.stack((np.zeros(vert_len, dtype=int), np.arange(1, vert_len + 1, dtype=int)), -1)
    return Controller(geometry.name, bind_matrix, inv_bind_matrix, bone_names, weights,
                      np.full(vert_len, 1, dtype=int), weight_indices, geometry)


def main():
    cmdline_convert(sys.argv[1:], '.dae', DaeConverter2)


if __name__ == '__main__':
    main()
