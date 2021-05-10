import os
import sys

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters import influence
from abmatt.converters import convert_lib
from abmatt.converters import dae as collada
from abmatt.converters import matrix as mtx
from abmatt.converters.controller import get_controller
from abmatt.converters.material import Material
from abmatt.converters.matrix import rotate_z_up_to_y_up


class DaeConverter(convert_lib.Converter):

    def load_model(self, model_name=None):
        self._start_loading(model_name)
        self.bones = {}
        self.bones_by_name = {}
        self.dae = dae = collada.Dae(self.mdl_file)
        materials = self.__parse_materials(dae.get_materials())
        material_names = {x.name for x in materials}
        self.controllers = []
        self.influences = influence.InfluenceManager()   # this is to track all influences, consolidating from each controller
        # geometry
        matrix = np.identity(4)
        if self.DETECT_FILE_UNITS:
            if not np.isclose(dae.unit_meter, 1.0):     # set the matrix scale to convert to meters
                for i in range(3):
                    matrix[i][i] = dae.unit_meter
        material_geometry_map = {}
        self.__parse_nodes(dae.get_scene(), material_geometry_map, matrix)
        self.__combine_bones_map()
        self.__parse_controllers(material_geometry_map)

        self._before_encoding()
        self.influences.encode_bone_weights(self.mdl0)
        for material in material_geometry_map:
            if material not in material_names:
                self._encode_material(material.Material(material))
                material_names.add(material)
            geometries = material_geometry_map[material]
            for x in geometries:
                self.__encode_geometry(x)
        self.import_textures_map = dae.get_images()
        return self._end_loading()

    def save_model(self, mdl0=None):
        base_name, mdl0 = self._start_saving(mdl0)
        mesh = collada.Dae(initial_scene_name=base_name)
        self.decoded_mats = [self.__decode_material(x, mesh) for x in mdl0.materials]
        # polygons
        polygons = mdl0.objects
        mesh.add_node(self.__decode_bone(mdl0.bones[0]))
        for polygon in polygons:
            mesh.add_node(self.__decode_geometry(polygon))
        for mat in self.decoded_mats:
            mesh.add_material(mat)
        self._end_saving(mesh)

    @staticmethod
    def __get_matrix(bone):
        return mtx.srt_to_matrix(bone.scale, bone.rotation, bone.translation)

    def __decode_bone(self, mdl0_bone, collada_parent=None, matrix=None):
        if len(self.bones) >= 1 and self.flags & self.SINGLE_BONE:
            return
        name = mdl0_bone.name
        self.bones[name] = mdl0_bone
        node = collada.ColladaNode(name, {'type': 'JOINT'})
        matrix = self.__get_matrix(mdl0_bone)
        node.matrix = matrix
        if collada_parent:
            collada_parent.nodes.append(node)
        if mdl0_bone.child:
            self.__decode_bone(mdl0_bone.child, node, node.matrix)
        if mdl0_bone.next:
            self.__decode_bone(mdl0_bone.next, collada_parent, matrix)
        return node

    def __decode_geometry(self, polygon):
        geo = super()._decode_geometry(polygon)
        name = polygon.name
        node = collada.ColladaNode(name)
        node.geometries.append(geo)
        node.controller = get_controller(geo)
        return node

    def __decode_material(self, material, mesh):
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
                if tex0 is None:
                    AutoFix.warn('No texture found matching {}'.format(layer))
                else:
                    map_path = layer + '.png'
                    mesh.add_image(layer, os.path.join(self.image_dir, map_path))
                    self.tex0_map[layer] = tex0
        return Material(material.name, diffuse_map, ambient_map, specular_map, material.xlu * 0.5)

    def __parse_controllers(self, material_geometry_map):
        for controller, matrix in self.controllers:
            self.__parse_controller(controller, matrix, material_geometry_map)

    def __parse_controller(self, controller, matrix, material_geometry_map):
        geometry, influences = controller.get_bound_geometry(self.bones, self.influences, matrix)
        if type(geometry) == list:
            for x in geometry:
                self.__add_geometry(x, material_geometry_map)
        else:
            self.__add_geometry(geometry, material_geometry_map)

    def __encode_geometry(self, geometry):
        if not self.dae.y_up:
            geometry.swap_y_z_axis()
        replace = 'Mesh'
        if geometry.name.endswith(replace) and len(replace) < len(geometry.name):
            geometry.name = geometry.name[:len(replace) * -1]
        super()._encode_geometry(geometry)

    def __add_bone(self, node, parent_bone=None, matrix=None):
        name = node.attrib['id']
        if name not in self.bones:
            if len(self.bones) and self.flags & self.SINGLE_BONE:  # Only add one if single bone enabled
                return
            else:
                if not self.dae.y_up:
                    matrix = rotate_z_up_to_y_up(matrix)
                self.bones[name] = bone = self.mdl0.add_bone(name, parent_bone)
                self.set_bone_matrix(bone, matrix)
            name = node.attrib.get('name')
            if name is not None and name not in self.bones_by_name:
                self.bones_by_name[name] = bone
            return bone

    def __add_geometry(self, geometry, material_geometry_map):
        geo = material_geometry_map.get(geometry.material_name)
        if geo is not None:
            if not geo[0].combine(geometry):
                geo.append(geometry)
                self.geometries.append(geometry)
        else:
            material_geometry_map[geometry.material_name] = [geometry]
            self.geometries.append(geometry)

    def __calc_node_matrix(self, node):
        return node.matrix
        # if self.dae.y_up:
        #     return node.matrix
        # rotation_matrix = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
        # return np.matmul(rotation_matrix, node.matrix)

    def __parse_nodes(self, nodes, material_geometry_map, matrix=None, parent_bone=None):
        for node in nodes:
            m = self.__calc_node_matrix(node)
            current_node_matrix = mtx.combine_matrices(matrix, m)
            new_parent_bone=None
            if node.controller:
                self.controllers.append((node.controller, current_node_matrix))
            elif node.geometries:
                for x in node.geometries:
                    if current_node_matrix is not None:
                        x.apply_matrix(current_node_matrix)
                    self.__add_geometry(x, material_geometry_map)
            elif node.attrib.get('type') == 'JOINT':
                new_parent_bone = self.__add_bone(node, parent_bone=parent_bone, matrix=current_node_matrix)
            self.__parse_nodes(node.nodes, material_geometry_map, current_node_matrix, new_parent_bone)

    def __combine_bones_map(self):
        """Adds the bones by name to bones (in case naming is different than id)"""
        for bone_name in self.bones_by_name:
            if not bone_name in self.bones:
                self.bones[bone_name] = self.bones_by_name[bone_name]

    def __parse_materials(self, materials):
        return [self._encode_material(material) for material in materials]



def main():
    cmdline_convert(sys.argv[1:], '.dae', DaeConverter)


if __name__ == '__main__':
    main()
