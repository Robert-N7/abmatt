import os

import numpy as np

from converters.convert_lib import Geometry, PointCollection, ColorCollection, Material, Controller
from converters.xml import XML, XMLNode
from datetime import datetime


class ColladaMap:
    def __init__(self, path, name=None, coordinate_id=0):
        self.texture = texture = XMLNode('texture')
        if not name:
            name = os.path.splitext(os.path.basename(path))[0]
        tex_id = name + '-image'
        texture.attributes['texture'] = tex_id
        texture.attributes['texcoord'] = 'CHANNEL' + str(coordinate_id)
        self.image = image = XMLNode('image', id=tex_id)
        image.attributes['name'] = name
        init_from = XMLNode('init_from', path)
        image.add_child(init_from)


class Collada:
    def __init__(self, filename=None):
        self.xml = XML(filename) if filename else self.__initialize_xml()
        self.__initialize_libraries()

    def write(self, filename):
        root = self.xml.root
        temp = root.children
        non_empty_libraries = [x for x in root.children if x.children]
        root.children = non_empty_libraries
        self.xml.write(filename)
        root.children = temp

    def get_element_by_id(self, id):
        return self.xml.get_element_by_id(id)

    def get_referenced_element(self, element, attribute_source):
        return self.get_element_by_id(element.attributes[attribute_source])

    def trace_technique_common(self, element):
        ele = element['technique_common']['accessor']
        data_type = ele['param'].attributes['type']
        return data_type, self.get_referenced_element(ele, 'source')

    def decode_controller(self, xml_controller):
        name = xml_controller.get_id()
        skin = xml_controller['skin']
        bind_shape_matrix = [float(x) for x in skin['bind_shape_matrix'].text.split()]
        joints = skin['joints']
        vertex_weights = skin['vertex_weights']
        vertex_weight_count = [float(x) for x  in vertex_weights['vcount'].text.split()]
        vertex_weight_indices = np.array([int(x) for x in vertex_weights['v'].text.split()], int)
        vertex_weight_indices = vertex_weight_indices.reshape((-1, 2))
        input_count = 0
        for input in vertex_weights.get_elements_by_name('input'):
            offset = int(input.attributes['offset'])
            semantic = input.attributes['semantic']
            if semantic == 'JOINT':
                if offset != 0:
                     vertex_weight_indices[:, [0, 1]] = vertex_weight_indices[:, [1, 0]]
                joints = self.get_referenced_element(input, 'source')
                data_type, joint_name_element = self.trace_technique_common(joints)
                joint_names = joint_name_element.text.split()
            elif semantic == 'WEIGHT':
                weight_xml = self.get_referenced_element(input, 'source')
                data_type, weight_xml_data = self.trace_technique_common(weight_xml)
                weights = np.array([float(x) for x in weight_xml_data.text.split()], float)
            else:
                raise ValueError('Unknown Semantic {} in controller {}'.format(semantic, name))
            input_count += 1
        assert input_count == 2
        return Controller(name, bind_shape_matrix, joint_names, weights, vertex_weight_count, vertex_weight_indices)

    def add_skin_controller(self, controller):
        controller_id = controller.name + '-controller'
        xml_controller = XMLNode('controller', id=controller_id, parent=self.controllers)
        xml_skin = XMLNode('skin', parent=xml_controller)
        xml_skin.attributes['source'] = '#' + controller.name + '-lib'
        bind_shape_matrix = XMLNode('bind_shape_matrix', ' '.join(controller.bind_shape_matrix.flatten()),
                                    parent=xml_skin)
        joint_source_id = controller_id + '-joints'
        joint_source = XMLNode('source', id=joint_source_id, parent=xml_skin)
        name_array_id = joint_source_id + '-array'
        name_array = XMLNode('Name_array', ' '.join(controller.bones), id=name_array_id,
                             parent=joint_source)
        bone_len = len(controller.bones)
        name_array.attributes['count'] = str(bone_len)
        self.__create_technique_common(name_array_id, bone_len, 'float4x4', joint_source)
        matrices_source_id = controller_id + '-matrices'
        matrices_source = XMLNode('source', id=matrices_source_id, parent=xml_skin)
        matrices_array_id = matrices_source_id + '-array'
        inv_bind_matrix = np.linalg.inv(controller.bind_shape_matrix).flatten()
        float_array = XMLNode('float_array', ' '.join(inv_bind_matrix), id=matrices_array_id, parent=matrices_source)
        float_array.attributes['count'] = 16 * bone_len
        self.__create_technique_common(matrices_array_id, bone_len, 'float4x4', matrices_source, 16)
        weight_source_id = controller_id + '-weights'
        weight_source = XMLNode('source', ' '.join(controller.weights.flatten()), id=weight_source_id, parent=xml_skin)
        float_array_id = weight_source_id + '-array'
        float_array = XMLNode('float_array', id=float_array_id, parent=weight_source)
        weight_count = len(controller.weights)
        float_array.attributes['count'] = str(weight_count)  # todo, vertex count or total weight?
        self.__create_technique_common(float_array_id, weight_count, 'float', weight_source)
        joints = XMLNode('joints', parent=xml_skin)
        self.__create_input_node('JOINT', joint_source_id, parent=joints)
        self.__create_input_node('INV_BIND_MATRIX', matrices_source_id, parent=joints)
        vertex_weights = XMLNode('vertex_weights', parent=xml_skin)
        vertex_weights.attributes['count'] = str(weight_count)  # todo check this
        self.__create_input_node('JOINT', joint_source_id, 0, vertex_weights)
        self.__create_input_node('WEIGHT', weight_source_id, 1, vertex_weights)
        vcount = XMLNode('vcount', ' '.join(controller.vertex_weight_counts), parent=vertex_weights)
        vw_data = XMLNode('v', ' '.join(controller.vertex_weight_indices.flatten()), parent=vertex_weights)
        return xml_controller

    def decode_geometry(self, xml_geometry):
        mesh = xml_geometry.children[0]
        tri_node = mesh.children[0]
        material_name = tri_node.attributes['material']
        inputs = tri_node.get_elements_by_tag('input')
        stride = len(inputs)
        indices = [int(x) for x in tri_node['p']]
        triangles = np.array(indices, np.int16).reshape((-1, 3, stride))
        vertices = normals = colors = None
        texcoords = []
        for input in inputs:
            decode_type, decoded_data = self.__decode_input(input, triangles)
            if decode_type == 'TEXCOORD':
                texcoords.append(decoded_data)
            elif decode_type == 'VERTEX':
                vertices = decoded_data
            elif decode_type == ' NORMAL':
                normals = decoded_data
            elif decode_type == 'COLOR':
                colors = decoded_data
        geometry = Geometry(xml_geometry.attributes['name'], material_name, triangles=triangles, vertices=vertices,
                            normals=normals, texcoords=texcoords, colors=colors)
        return geometry

    def add_geometry(self, geometry):
        """
        geometry: convert_lib geometry
        """
        name = geometry.name
        material_name = geometry.material.name
        vertices = geometry.vertices
        normals = geometry.normals
        colors = geometry.colors
        texcoords = geometry.texcoords
        geo_xml = XMLNode('geometry', id=name + '-lib', name=name)
        mesh = XMLNode('mesh')
        offset = 0
        triangles = XMLNode('triangles')
        triangles.attributes['material'] = material_name
        tris = [vertices.face_indices]
        triangles.attributes['count'] = len(tris[0])
        geo_xml.add_child(mesh)
        source_name = name + '-POSITION'
        mesh.add_child(self.__create_source(source_name, vertices.points, ('X', 'Y', 'Z')))
        triangles.add_child(self.__create_input_node('VERTEX', source_name, offset))
        offset += 1
        if normals:
            source_name = name + '-NORMAL0'
            mesh.add_child(self.__create_source(source_name, normals.points, ('X', 'Y', 'Z')))
            triangles.add_child(self.__create_input_node('NORMAL', source_name, offset))
            tris.append(normals.face_indices)
            offset += 1
        if colors:
            source_name = name + '-COLOR'
            mesh.add_child(self.__create_source(source_name, colors.rgba_colors, ('R', 'G', 'B', 'A')))
            triangles.add_child(self.__create_input_node('COLOR', source_name, offset))
            tris.append(colors.face_indices)
            offset += 1
        for i in range(len(texcoords)):
            texcoord = texcoords[i]
            source_name = name + '-UV' + str(i)
            mesh.add_child(self.__create_source(source_name, texcoord.points, ('S', 'T')))
            input_node = self.__create_input_node('TEXCOORD', source_name, offset)
            input_node.attributes['set'] = i
            triangles.add_child(input_node)
            tris.append(texcoord.face_indices)
            offset += 1
        data = np.stack(tris, -1).flatten()
        tri_data = XMLNode('p', ' '.join(data))
        triangles.add_child(tri_data)
        vert_node = XMLNode('vertices', id=name + '-VERTEX')
        input_node = self.__create_input_node('POSITION', name + '-POSITION')
        vert_node.add_child(input_node)
        mesh.add_child(vert_node)
        mesh.add_child(triangles)
        self.geometries.append(geo_xml)
        return geo_xml

    def __try_get_texture(self, xml_node):
        texture = xml_node['texture']
        if texture:
            return self.get_element_by_id(texture.attributes['texture'])['init_from']

    def decode_material(self, material_xml):
        effect = self.get_referenced_element(material_xml['instance_effect'], 'url')
        shader = effect['profile_COMMON']['technique'].children[0]
        diffuse = self.__try_get_texture(shader['diffuse'])
        ambient = self.__try_get_texture(shader['ambient'])
        specular = self.__try_get_texture(shader['specular'])
        transparency = float(shader['transparency']['float'])
        material = Material(material_xml.attributes['id'], diffuse, ambient, specular, transparency)
        return material

    def add_material(self, material):
        diffuse_map = (0.6, 0.6, 0.6, 1.0) if not material.diffuse_map else ColladaMap(material.diffuse_map)
        ambient_map = (0.6, 0.6, 0.6, 1.0) if not material.ambient_map else ColladaMap(material.ambient_map)
        specular_map = (0.6, 0.6, 0.6, 1.0) if not material.specular_map else ColladaMap(material.specular_map)
        transparency = material.transparency
        name = material.name
        material = XMLNode('material')
        material.attributes['id'] = material.attributes['name'] = name
        self.materials.add_child(material)
        effect_id = name + '-fx'
        instance_effect = XMLNode('instance_effect')
        material.add_child(instance_effect)
        instance_effect.attributes['url'] = '#' + effect_id
        effect = XMLNode('effect')
        effect.attributes['id'] = effect_id
        effect.attributes['name'] = name
        profile_common = XMLNode('profile_COMMON')
        effect.add_child(profile_common)
        technique = XMLNode('technique')
        technique.attributes['sid'] = 'standard'
        profile_common.add_child(technique)
        shader = XMLNode('phong')
        technique.add_child(shader)
        shader.add_child(self.__get_default_shader_color('emission'))
        if type(ambient_map) == ColladaMap:
            shader.add_child(ambient_map.texture)
            self.images.add_child(ambient_map.image)
        else:
            shader.add_child(self.__get_default_shader_color('ambient', ambient_map))
        if type(diffuse_map) == ColladaMap:
            shader.add_child(diffuse_map.texture)
            self.images.add_child(diffuse_map.image)
        else:
            shader.add_child(self.__get_default_shader_color('diffuse', diffuse_map))
        if type(specular_map) == ColladaMap:
            shader.add_child(specular_map.texture)
            self.images.add_child(specular_map.image)
        else:
            shader.add_child(self.__get_default_shader_color('specular', specular_map))
        shader.add_child(self.__get_default_shader_float('shininess', 1.071773))
        shader.add_child(self.__get_default_shader_color('reflective'))
        shader.add_child(self.__get_default_shader_float('reflectivity', 1.0))
        node = self.__get_default_shader_color('transparent', (1.0, 1.0, 1.0, 1.0))
        node.attributes['opaque'] = 'RGB_ZERO'
        shader.add_child(node)
        shader.add_child(self.__get_default_shader_float('transparency', transparency))
        return material

    def __initialize_libraries(self):
        libraries = ('visual_scenes', 'controllers', 'images', 'effects',
                     'materials', 'geometries')
        root_children = self.xml.root.children
        for library in root_children:
            tag = library.tag
            if 'library' in tag:
                self.__setattr__(tag.lstrip('library_'), library)
        for library in libraries:
            if not self.__getattribute__(library):
                node = XMLNode('library_' + library)
                root_children.append(node)
                self.__setattr__(library, node)

    @staticmethod
    def __initialize_assets():
        asset = XMLNode('asset')
        contributor = XMLNode('contributor')
        authoring_tool = XMLNode('authoring_tool', 'abmatt COLLADA exporter')
        contributor.add_child(authoring_tool)
        time_stamp = datetime.now()
        created = XMLNode('created', time_stamp)
        modified = XMLNode('modified', time_stamp)
        up_axis = XMLNode('up_axis', 'Y_UP')
        asset.add_child(up_axis)
        asset.add_child(created)
        asset.add_child(modified)
        asset.children.append(contributor)
        return asset

    @staticmethod
    def __initialize_xml():
        xml = XML()
        root = XMLNode('COLLADA')
        root.attributes['xmlns'] = 'http://www.collada.org/2005/11/COLLADASchema'
        root.attributes['version'] = '1.4.1'
        root.children.append(Collada.__initialize_assets())
        xml.root = root
        return xml

    @staticmethod
    def __get_default_shader_color(name, iterable=(0.0, 0.0, 0.0, 1.0)):
        shader_color = XMLNode(name)
        text = ' '.join(iterable)
        color = XMLNode('color', text)
        color.attributes['sid'] = name
        shader_color.add_child(color)
        return shader_color

    @staticmethod
    def __get_default_shader_float(name, fl=0.0):
        node = XMLNode(name)
        fl = XMLNode('float', str(fl))
        fl.attributes['sid'] = name
        node.add_child(fl)
        return node

    @staticmethod
    def __create_source(name, data_collection, params):
        technique_common = XMLNode('technique_common')
        accessor = XMLNode('accessor')
        accessor.attributes['source'] = '#' + name + '-array'
        point_len = len(data_collection)
        accessor.attributes['count'] = point_len
        stride = len(data_collection[0])
        accessor.attributes['stride'] = stride
        for letter in params:
            param = XMLNode('param', name=letter)
            param.attributes['type'] = 'float'
            accessor.add_child(param)
        source = XMLNode('source', id=name)
        text = '\n'
        for x in data_collection:
            text += ' '.join(x) + '\n'
        source_array = XMLNode('float_array', text, id=name + '-array')
        source_array.attributes['count'] = stride * point_len
        source.add_child(source_array)
        source.add_child(technique_common)
        return source

    @staticmethod
    def __create_input_node(semantic, source, offset=None, parent=None):
        node = XMLNode('input', parent=parent)
        node.attributes['semantic'] = semantic
        if offset:
            node.attributes['offset'] = str(offset)
        node.attributes['source'] = source
        return node

    def __decode_input(self, input, triangles):
        decoded_type = input.attributes['semantic']
        source = self.get_referenced_element(input, 'source')
        while source.tag != 'source':
            source = self.get_referenced_element(input, 'source')
        accessor = source['technique_common']['accessor']
        stride = accessor.attributes['stride']
        float_array = self.get_referenced_element(accessor, 'source')
        points = np.array([float(x) for x in float_array.text.split()])
        if stride:
            points.reshape((-1, int(stride)))
        offset = int(input.attributes['offset'])
        if decoded_type == 'COLOR':
            return decoded_type, ColorCollection(points, triangles[:, :, offset], normalize=True)
        elif decoded_type in ('VERTEX', 'NORMAL', 'TEXCOORD'):
            return decoded_type, PointCollection(points, triangles[:, :, offset])
        else:
            raise ValueError('Unknown collada input {}'.format(decoded_type))

    @staticmethod
    def __create_technique_common(source, count, type, parent_node, stride=None):
        technique_common = XMLNode('technique_common', parent=parent_node)
        accessor = XMLNode('accessor', parent=technique_common)
        accessor.attributes['source'] = '#' + source
        accessor.attributes['count'] = str(count)
        if stride:
            accessor.attributes['stride'] = str(stride)
        param = XMLNode('param', parent=accessor)
        param.attributes['type'] = type
        return technique_common

