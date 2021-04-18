from datetime import datetime

import numpy as np
from lxml import etree

from abmatt.converters.colors import ColorCollection
from abmatt.converters.controller import Controller
from abmatt.converters.convert_lib import float_to_str
from abmatt.converters.geometry import Geometry
from abmatt.converters.material import Material
from abmatt.converters.matrix import scale_matrix, rotate_matrix, translate_matrix
from abmatt.converters.points import PointCollection


def XMLNode(tag, text=None, id=None, name=None, parent=None):
    if parent is not None:
        ele = etree.SubElement(parent, tag)
    else:
        ele = etree.Element(tag)
    if text is not None:
        ele.text = text
    if id is not None:
        ele.attrib['id'] = id
    if name is not None:
        ele.attrib['name'] = name
    return ele


def first(element, item):
    for x in element.iter(item):
        return x


def get_id(element):
    return element.attrib['id']


class ColladaNode:
    def __init__(self, name, attributes=None):
        self.name = name
        self.attrib = attributes
        self.extra = self.matrix = self.controller = None
        self.geometries = []
        self.nodes = []

    def get_matrix(self):
        if self.matrix is None:
            self.matrix = np.identity(4)
        return self.matrix

    def scale(self, scale):
        self.matrix = scale_matrix(self.get_matrix(), scale)

    def rotate(self, rotation):
        self.matrix = rotate_matrix(self.get_matrix(), rotation)

    def translate(self, translation):
        self.matrix = translate_matrix(self.get_matrix(), translation)


class Dae:
    def __init__(self, filename=None, initial_scene_name=None):
        self.y_up = True
        self.unit_meter = 1
        self.elements_by_id = {}
        if filename:
            with open(filename) as f:
                self.xml = self.__read_xml(f)
            self.__init_elements_by_id(self.xml.getroot())
        else:
            self.xml = self.__initialize_xml()
        self.__initialize_libraries(initial_scene_name)

    def __init_elements_by_id(self, element):
        id = element.get('id')
        if id is not None:
            self.elements_by_id[id] = element
        for x in element:
            self.__init_elements_by_id(x)

    def write(self, filename):
        self.xml.write(filename, pretty_print=True, xml_declaration=True, encoding='utf-8')

    def get_scene(self):
        self.node_ids = set()
        nodes = []
        for x in self.scene:
            node = self.decode_node(x)
            if node is not None:
                nodes.append(node)
        return nodes

    def get_materials(self):
        return [self.decode_material(x) for x in self.materials]

    def get_image_path(self, image_node):
        init = first(image_node, 'init_from')
        path = init.text
        if not path:
            path = init[0].text
        return path

    def get_images(self):
        images = {}
        for x in self.images:
            name = x.attrib.get('name')
            if not name:
                name = get_id(x)
            images[name] = self.get_image_path(x)
        return images

    def get_element_by_id(self, id):
        return self.elements_by_id.get(id)

    @staticmethod
    def search_library_by_id(library, id):
        for x in library:
            if x.get('id') == id:
                return x

    def get_referenced_element(self, element, attribute_source):
        return self.get_element_by_id(element.attrib[attribute_source][1:])

    def trace_technique_common(self, element):
        ele = first(first(element, 'technique_common'), 'accessor')
        data_type = first(ele, 'param').attrib['type']
        return data_type, self.get_referenced_element(ele, 'source')

    def decode_node(self, xml_node):
        node = ColladaNode(first(xml_node, 'id'), xml_node.attrib)
        node_id = node.attrib.get('id')
        if node_id is not None and node_id in self.node_ids:
            return None
        self.node_ids.add(node_id)
        for child in xml_node:
            if child.tag == 'instance_controller':
                geom = self.get_referenced_element(child, 'url')
                node.controller = self.decode_controller(geom, self.__get_bound_material(child))
            elif child.tag == 'instance_geometry':
                target = self.__get_bound_material(child)
                node.geometries.append(self.decode_geometry(self.get_referenced_element(child, 'url'), target))
            elif child.tag == 'matrix':
                node.matrix = np.array([float(x) for x in child.text.split()]).reshape((4, 4))
            elif child.tag == 'extra':
                node.extra = child
            elif child.tag == 'node':
                n = self.decode_node(child)
                if n is not None:
                    node.nodes.append(n)
            elif child.tag == 'scale':
                node.scale([float(x) for x in child.text.split()])
            elif child.tag == 'rotate':
                rotation = [float(x) for x in child.text.split()]
                angle = rotation.pop(-1)
                node.rotate([x * angle for x in rotation])
            elif child.tag == 'translate':
                node.translate([float(x) for x in child.text.split()])
        return node

    def add_node(self, node, parent=None):
        if parent is None:
            parent = self.scene
        xml_node = XMLNode('node', id=node.name, name=node.name, parent=parent)
        if node.attrib:
            att = node.attrib
            for key in att:
                xml_node.attrib[key] = att[key]
        xml_node.attrib['sid'] = node.name
        if node.matrix is not None:
            matrix_xml = XMLNode('matrix', ' '.join([float_to_str(x) for x in node.matrix.flatten()]), parent=xml_node)
            matrix_xml.attrib['sid'] = 'matrix'
        if node.extra is not None:
            xml_node.append(node.extra)
        if node.controller is not None:
            controller_node = XMLNode('instance_controller', parent=xml_node)
            controller_node.attrib['url'] = '#' + get_id(self.add_skin_controller(node.controller))
            self.__bind_material(controller_node, node.controller.geometry.material_name)
        elif node.geometries:
            for geometry in node.geometries:
                geometry_node = XMLNode('instance_geometry', parent=xml_node)
                geometry_node.attrib['url'] = '#' + get_id(self.add_geometry(geometry))
                self.__bind_material(geometry_node, geometry.material_name)
        for n in node.nodes:
            self.add_node(n, xml_node)
        return xml_node

    def decode_controller(self, xml_controller, bind_material=None):
        name = get_id(xml_controller)
        skin = first(xml_controller, 'skin')
        ref = self.get_referenced_element(skin, 'source')
        if ref.tag != 'geometry':  # fix for badly formed xml
            ref = self.search_library_by_id(self.geometries, skin.attrib['source'][1:])
        geometry = self.decode_geometry(ref, bind_material)
        bind_shape_matrix = np.array([float(x) for x in first(skin, 'bind_shape_matrix').text.split()],
                                     dtype=float).reshape((4, 4))
        joints = first(skin, 'joints')
        for input in joints:
            semantic = input.attrib['semantic']
            if semantic == 'INV_BIND_MATRIX':
                matrices = self.get_referenced_element(input, 'source')
                data_type, float_arr = self.trace_technique_common(matrices)
                inv_bind_matrices = np.array([float(x) for x in float_arr.text.split()], float)
                inv_bind_matrices.reshape((-1, 4, 4))
        vertex_weights = first(skin, 'vertex_weights')
        vertex_weight_count = [int(x) for x in first(vertex_weights, 'vcount').text.split()]
        try:
            vertex_weight_indices = np.array([int(x) for x in first(vertex_weights, 'v').text.split()], int)
            vertex_weight_indices = vertex_weight_indices.reshape((-1, 2))
        except AttributeError:
            vertex_weight_indices = None
        input_count = 0
        for input in vertex_weights.iter('input'):
            offset = int(input.attrib['offset'])
            semantic = input.attrib['semantic']
            if semantic == 'JOINT':
                if offset != 0:
                    vertex_weight_indices[:, [0, 1]] = vertex_weight_indices[:, [1, 0]]
                joints = self.get_referenced_element(input, 'source')
                data_type, joint_name_element = self.trace_technique_common(joints)
                joint_names = joint_name_element.text.split()
            elif semantic == 'WEIGHT':
                weight_xml = self.get_referenced_element(input, 'source')
                data_type, weight_xml_data = self.trace_technique_common(weight_xml)
                try:
                    weights = np.array([float(x) for x in weight_xml_data.text.split()], float)
                except AttributeError:
                    weights = np.array(1.0)
            else:
                raise ValueError('Unknown Semantic {} in controller {}'.format(semantic, name))
            input_count += 1
        assert input_count == 2
        return Controller(name, bind_shape_matrix, inv_bind_matrices, joint_names, weights, vertex_weight_count,
                          vertex_weight_indices, geometry)

    def add_skin_controller(self, controller):
        controller_id = controller.name + '-controller'
        xml_controller = XMLNode('controller', id=controller_id, parent=self.controllers)
        xml_skin = XMLNode('skin', parent=xml_controller)
        xml_skin.attrib['source'] = '#' + get_id(self.add_geometry(controller.geometry))
        bind_shape_matrix = XMLNode('bind_shape_matrix', ' '.join([float_to_str(x) for \
                                                                   x in controller.bind_shape_matrix.flatten()]),
                                    parent=xml_skin)
        joint_source_id = controller_id + '-joints'
        joint_source = XMLNode('source', id=joint_source_id, parent=xml_skin)
        name_array_id = joint_source_id + '-array'
        name_array = XMLNode('Name_array', ' '.join(controller.bones), id=name_array_id, parent=joint_source)
        bone_len = len(controller.bones)
        name_array.attrib['count'] = str(bone_len)
        self.__create_technique_common(name_array_id, bone_len, 'name', joint_source)
        matrices_source_id = controller_id + '-matrices'
        matrices_source = XMLNode('source', id=matrices_source_id, parent=xml_skin)
        matrices_array_id = matrices_source_id + '-array'
        inv_bind_matrix = controller.inv_bind_matrix.flatten()
        float_array = XMLNode('float_array', ' '.join([float_to_str(x) for x in inv_bind_matrix]), id=matrices_array_id,
                              parent=matrices_source)
        float_array.attrib['count'] = str(16 * bone_len)
        self.__create_technique_common(matrices_array_id, bone_len, 'float4x4', matrices_source, 16)
        weight_source_id = controller_id + '-weights'
        weight_source = XMLNode('source',
                                id=weight_source_id, parent=xml_skin)
        float_array_id = weight_source_id + '-array'
        float_array = XMLNode('float_array', ' '.join([float_to_str(x) for x in controller.weights.flatten()]),
                              id=float_array_id, parent=weight_source)
        weight_count = len(controller.weights)
        float_array.attrib['count'] = str(weight_count)  # todo, vertex count or total weight?
        self.__create_technique_common(float_array_id, weight_count, 'float', weight_source)
        joints = XMLNode('joints', parent=xml_skin)
        self.__create_input_node('JOINT', joint_source_id, parent=joints)
        self.__create_input_node('INV_BIND_MATRIX', matrices_source_id, parent=joints)
        vertex_weights = XMLNode('vertex_weights', parent=xml_skin)
        vertex_weights.attrib['count'] = str(len(controller.vertex_weight_counts))
        self.__create_input_node('JOINT', joint_source_id, 0, vertex_weights)
        self.__create_input_node('WEIGHT', weight_source_id, 1, vertex_weights)
        vcount = XMLNode('vcount', ' '.join([str(x) for x in controller.vertex_weight_counts]), parent=vertex_weights)
        vw_data = XMLNode('v', ' '.join([str(x) for x in controller.vertex_weight_indices.flatten()]),
                          parent=vertex_weights)
        return xml_controller

    def decode_geometry(self, xml_geometry, material_name=None):
        mesh = first(xml_geometry, 'mesh')
        tri_node = first(mesh, 'triangles')
        if not material_name:
            material_name = tri_node.attrib.get('material')
            if not material_name:
                for attrib in xml_geometry.attrib:
                    material_name = xml_geometry.attrib[attrib] + '-mat'
                    break
        inputs = []
        stride = 0
        uniqueOffsets = []
        indices = []
        for input in tri_node.iter('input'):
            offset = int(input.attrib['offset'])
            if offset not in uniqueOffsets:   # duplicate
                uniqueOffsets.append(offset)
            inputs.append(input)
        for x in tri_node.iter('p'):
            indices.extend([int(index) for index in x.text.split()])
        vertices = normals = colors = None
        texcoords = []
        data_inputs = []
        data_types = []
        offsets = []
        for input in inputs:
            offset = int(input.attrib['offset'])
            source = self.get_referenced_element(input, 'source')
            if source.tag != 'source':
                for x in source.iter('input'):
                    source = self.get_referenced_element(x, 'source')
                    data_inputs.append(self.__decode_source(source))
                    data_types.append(x.attrib['semantic'])
                    offsets.append(offset)
                    stride += 1
            else:
                data_inputs.append(self.__decode_source(source))
                data_types.append(input.attrib['semantic'])
                offsets.append(offset)
                stride += 1
        triangles = np.array(indices, np.uint16).reshape((-1, 3, len(uniqueOffsets)))
        count = tri_node.attrib.get('count')
        if count is not None and int(count) != triangles.shape[0]:
            raise ValueError('Failed to parse {} triangles of unexpected shape, expected {} and got {}'.format(material_name, count, triangles.shape[0]))

        for i in range(len(data_inputs)):
            decode_type = data_types[i]
            face_indices = np.copy(triangles[:, :, offsets[i]])
            if decode_type == 'TEXCOORD':
                texcoords.append(PointCollection(data_inputs[i], face_indices))
            elif decode_type == 'POSITION':
                vertices = PointCollection(data_inputs[i], face_indices)
            elif decode_type == 'NORMAL':
                normals = PointCollection(data_inputs[i], face_indices)
            elif decode_type == 'COLOR':
                colors = ColorCollection(data_inputs[i], face_indices, normalize=True)
            else:
                raise ValueError('Unknown semantic {}'.format(decode_type))
        name = xml_geometry.attrib.get('name')
        if not name:
            name = get_id(xml_geometry)
        geometry = Geometry(name, material_name, vertices=vertices, texcoords=texcoords, normals=normals, colors=colors,
                            triangles=None)
        return geometry

    def add_geometry(self, geometry):
        """
        geometry: convert_lib geometry
        """
        name = geometry.name
        material_name = geometry.material_name
        vertices = geometry.vertices
        normals = geometry.normals
        colors = geometry.colors
        texcoords = geometry.texcoords
        geo_xml = XMLNode('geometry', id=name + '-lib', name=name, parent=self.geometries)
        mesh = XMLNode('mesh', parent=geo_xml)
        offset = 0
        tris = [vertices.face_indices]
        triangles = XMLNode('triangles')
        triangles.attrib['material'] = material_name
        triangles.attrib['count'] = str(len(tris[0]))
        source_name = name + '-POSITION'
        mesh.append(self.__create_source(source_name, vertices.points, ('X', 'Y', 'Z')))
        triangles.append(self.__create_input_node('VERTEX', name + '-VERTEX', offset))
        offset += 1
        if normals:
            source_name = name + '-NORMAL0'
            mesh.append(self.__create_source(source_name, normals.points, ('X', 'Y', 'Z')))
            triangles.append(self.__create_input_node('NORMAL', source_name, offset))
            tris.append(normals.face_indices)
            offset += 1
        if colors:
            source_name = name + '-COLOR'
            mesh.append(self.__create_source(source_name, colors.denormalize(), ('R', 'G', 'B', 'A')))
            triangles.append(self.__create_input_node('COLOR', source_name, offset))
            tris.append(colors.face_indices)
            offset += 1
        for i in range(len(texcoords)):
            texcoord = texcoords[i]
            source_name = name + '-UV' + str(i)
            mesh.append(self.__create_source(source_name, texcoord.points, ('S', 'T')))
            input_node = self.__create_input_node('TEXCOORD', source_name, offset)
            input_node.attrib['set'] = str(i)
            triangles.append(input_node)
            tris.append(texcoord.face_indices)
            offset += 1
        data = np.stack(tris, -1).flatten()
        tri_data = XMLNode('p', ' '.join([str(x) for x in data]), parent=triangles)
        vert_node = XMLNode('vertices', id=name + '-VERTEX', parent=mesh)
        input_node = self.__create_input_node('POSITION', name + '-POSITION')
        vert_node.append(input_node)
        mesh.append(triangles)
        return geo_xml

    @staticmethod
    def get_element_by_sid(sid, containing_element):
        for x in containing_element:
            if x.attrib['sid'] == sid:
                return x

    def decode_material(self, material_xml):
        effect = self.get_referenced_element(first(material_xml, 'instance_effect'), 'url')
        profile_common = first(effect, 'profile_COMMON')
        shader = first(profile_common, 'technique')[0]
        # possibly better to iterate through children?
        diffuse = self.__try_get_texture(first(shader, 'diffuse'), profile_common)
        ambient = self.__try_get_texture(first(shader, 'ambient'), profile_common)
        specular = self.__try_get_texture(first(shader, 'specular'), profile_common)
        transparency = 0
        transparency_node = first(shader, 'transparency')
        if transparency_node is not None:
            transparency = float(first(transparency_node, 'float').text)
        material = Material(material_xml.attrib['id'], diffuse, ambient, specular, transparency)
        return material

    def add_image(self, name, path):
        image = XMLNode('image', id=name + '-image', name=name, parent=self.images)
        init_from = XMLNode('init_from', path, parent=image)
        return image

    def __add_sampler(self, profile_common, name, samplers, swrap='WRAP', twrap='WRAP',
                      minfilter='LINEAR_MIPMAP_LINEAR'):
        if name is None or name in samplers:
            return
        surface_name = name + '-surface'
        new_param = XMLNode('newparam', parent=profile_common)
        new_param.attrib['sid'] = surface_name
        surface = XMLNode('surface', parent=new_param)
        surface.attrib['type'] = '2D'
        image_id = name + '-image'
        init_from = XMLNode('init_from', image_id, parent=surface)
        new_param = XMLNode('newparam', parent=profile_common)
        new_param.attrib['sid'] = name + '-sampler'
        sampler2d = XMLNode('sampler2D', parent=new_param)
        source = XMLNode('source', surface_name, parent=sampler2d)
        samplers.add(name)

    def add_material(self, material):
        transparency = material.transparency
        name = material.name
        material_node = XMLNode('material', id=name, name=name, parent=self.materials)
        effect_id = name + '-fx'
        instance_effect = XMLNode('instance_effect')
        material_node.append(instance_effect)
        instance_effect.attrib['url'] = '#' + effect_id
        effect = XMLNode('effect', id=effect_id, name=name, parent=self.effects)
        profile_common = XMLNode('profile_COMMON', parent=effect)
        technique = XMLNode('technique')
        technique.attrib['sid'] = 'COMMON'
        shader = XMLNode('phong', parent=technique)
        shader.append(self.__get_default_shader_color('emission'))
        i = 0
        maps = set()
        i += self.__add_shader_map(shader, 'diffuse', material.diffuse_map, i)
        self.__add_sampler(profile_common, material.diffuse_map, maps)
        i += self.__add_shader_map(shader, 'ambient', material.ambient_map, i)
        self.__add_sampler(profile_common, material.ambient_map, maps)
        self.__add_shader_map(shader, 'specular', material.specular_map, i)
        self.__add_sampler(profile_common, material.specular_map, maps)
        shader.append(self.__get_default_shader_float('shininess', 1.071773))
        shader.append(self.__get_default_shader_color('reflective'))
        shader.append(self.__get_default_shader_float('reflectivity', 1.0))
        node = self.__get_default_shader_color('transparent', (1.0, 1.0, 1.0, 1.0))
        node.attrib['opaque'] = 'RGB_ZERO'
        profile_common.append(technique)
        shader.append(node)
        shader.append(self.__get_default_shader_float('transparency', transparency))
        return material_node

    def __parse_assets(self, assets):
        for x in assets:
            if x.tag == 'up_axis':
                self.y_up = True if x.text == 'Y_UP' else False
            elif x.tag == 'unit':
                try:
                    self.unit_meter = float(x.attrib['meter'])
                except (ValueError, AttributeError):
                    pass

    @staticmethod
    def __read_xml(file):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file, parser)
        root = tree.getroot()
        for elem in root.getiterator():
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i + 1:]
        return tree

    def __initialize_libraries(self, initial_name):
        libraries = ('images', 'materials', 'effects',
                     'geometries', 'controllers', 'visual_scenes')
        root = self.xml.getroot()
        lib_str = 'library_'
        start = len(lib_str)
        for library in root:
            tag = library.tag
            if tag.startswith(lib_str):
                self.__setattr__(tag[start:], library)
            elif tag == 'asset':
                self.__parse_assets(library)
        for library in libraries:
            if not hasattr(self, library):
                node = XMLNode('library_' + library)
                root.append(node)
                self.__setattr__(library, node)
        if initial_name:
            scene_id = initial_name + '-scene'
            self.scene = XMLNode('visual_scene', id=scene_id, name=initial_name, parent=self.visual_scenes)
            scene = XMLNode('scene', parent=root)
            instance_scene = XMLNode('instance_visual_scene', parent=scene)
            instance_scene.attrib['url'] = '#' + scene_id
        else:
            self.scene = self.get_referenced_element(
                first(first(root, 'scene'), 'instance_visual_scene'), 'url')

    def __initialize_assets(self, root):
        asset = XMLNode('asset', parent=root)
        contributor = XMLNode('contributor', parent=asset)
        authoring_tool = XMLNode('authoring_tool', 'ABMATT COLLADA exporter v0.9.42', parent=contributor)
        time_stamp = datetime.now()
        created = XMLNode('created', str(time_stamp), parent=asset)
        modified = XMLNode('modified', str(time_stamp), parent=asset)
        units = XMLNode('unit', name='centimeter', parent=asset)
        units.attrib['meter'] = str(self.unit_meter)
        up = 'Y_UP' if self.y_up else 'Z_UP'
        up_axis = XMLNode('up_axis', up, parent=asset)

    def __initialize_xml(self):
        root = XMLNode('COLLADA')
        root.attrib['xmlns'] = 'http://www.collada.org/2005/11/COLLADASchema'
        root.attrib['version'] = '1.4.1'
        xml = etree.ElementTree(root)
        self.__initialize_assets(root)
        return xml

    @staticmethod
    def __get_default_shader_color(name, iterable=(0.0, 0.0, 0.0, 1.0)):
        shader_color = XMLNode(name)
        text = ' '.join([float_to_str(x) for x in iterable])
        color = XMLNode('color', text)
        color.attrib['sid'] = name
        shader_color.append(color)
        return shader_color

    @staticmethod
    def __get_default_shader_float(name, fl=0.0):
        node = XMLNode(name)
        fl = XMLNode('float', float_to_str(fl), parent=node)
        fl.attrib['sid'] = name
        return node

    @staticmethod
    def __create_source(name, data_collection, params):
        source = XMLNode('source', id=name)
        text = ''
        for x in data_collection:
            text += ' '.join([float_to_str(y) for y in x.flatten()]) + ' '
        source_array = XMLNode('float_array', text, id=name + '-array', parent=source)
        technique_common = XMLNode('technique_common', parent=source)
        accessor = XMLNode('accessor', parent=technique_common)
        accessor.attrib['source'] = '#' + name + '-array'
        point_len = len(data_collection)
        accessor.attrib['count'] = str(point_len)
        stride = len(data_collection[0])
        accessor.attrib['stride'] = str(stride)
        for letter in params:
            param = XMLNode('param', name=letter, parent=accessor)
            param.attrib['type'] = 'float'
        source_array.attrib['count'] = str(stride * point_len)
        return source

    @staticmethod
    def __create_input_node(semantic, source, offset=None, parent=None):
        node = XMLNode('input', parent=parent)
        node.attrib['semantic'] = semantic
        if offset is not None:
            node.attrib['offset'] = str(offset)
        node.attrib['source'] = '#' + source
        return node

    def __decode_input(self, input, triangles):
        decoded_type = input.attrib['semantic']
        source = self.get_referenced_element(input, 'source')
        while source.tag != 'source':
            source = self.get_referenced_element(first(source, 'input'), 'source')
        accessor = first(first(source, 'technique_common'), 'accessor')
        stride = accessor.attrib['stride']
        float_array = self.get_referenced_element(accessor, 'source')
        points = np.array([float(x) for x in float_array.text.split()])
        if stride:
            points = points.reshape((-1, int(stride)))
        offset = int(input.attrib['offset'])
        if decoded_type == 'COLOR':
            return decoded_type, ColorCollection(points, triangles[:, :, offset], normalize=True)
        elif decoded_type in ('VERTEX', 'NORMAL', 'TEXCOORD'):
            return decoded_type, PointCollection(points, triangles[:, :, offset])
        else:
            raise ValueError('Unknown collada input {}'.format(decoded_type))

    def __decode_source(self, source):
        data = np.array([float(x) for x in first(source, 'float_array').text.split()], dtype=float)
        accessor = first(first(source, 'technique_common'), 'accessor')
        stride = accessor.attrib.get('stride')
        if stride:
            data = data.reshape((-1, int(stride)))
        return data

    @staticmethod
    def __create_technique_common(source, count, type, parent_node, stride=None):
        technique_common = XMLNode('technique_common', parent=parent_node)
        accessor = XMLNode('accessor', parent=technique_common)
        accessor.attrib['source'] = '#' + source
        accessor.attrib['count'] = str(count)
        if stride:
            accessor.attrib['stride'] = str(stride)
        param = XMLNode('param', parent=accessor)
        param.attrib['type'] = type
        return technique_common

    @staticmethod
    def __bind_material(node, material_name):
        bind_mat = XMLNode('bind_material', parent=node)
        tech_common = XMLNode('technique_common', parent=bind_mat)
        instance_mat = XMLNode('instance_material', parent=tech_common)
        instance_mat.attrib['symbol'] = material_name
        instance_mat.attrib['target'] = '#' + material_name
        return bind_mat

    @staticmethod
    def __add_shader_map(shader, map_type='diffuse', map=None, texcoord=0):
        if map is None:
            map = (0.3, 0.3, 0.3, 1)
        if type(map) == tuple:
            shader.append(Dae.__get_default_shader_color(map_type, map))
            return False
        else:
            map_node = XMLNode(map_type, parent=shader)
            tex_node = XMLNode('texture', parent=map_node)
            tex = map + '-sampler'
            tex_node.attrib['texture'] = tex
            tex_node.attrib['texcoord'] = 'CHANNEL' + str(texcoord)
            return True

    def __try_get_texture(self, map_xml_node, profile_common):
        if map_xml_node is None:
            return map_xml_node
        texture = first(map_xml_node, 'texture')
        if texture is not None:
            id = texture.attrib['texture']
            image = self.get_element_by_id(id)
            if image is None:
                sampler = self.get_element_by_sid(id, profile_common)
                surface_id = first(first(sampler, 'sampler2D'), 'source').text
                surface_param = self.get_element_by_sid(surface_id, profile_common)
                init_from = first(first(surface_param, 'surface'), 'init_from')
                image_id = init_from.text
                if not image_id:
                    image_id = init_from[0].text
                image = self.get_element_by_id(image_id)
            init_from = first(image, 'init_from')
            image_path = init_from.text
            if not image_path:
                image_path = init_from[0].text
            return image_path

    @staticmethod
    def __get_bound_material(node):
        try:
            bound_material = first(first(first(node, 'bind_material'), 'technique_common'), 'instance_material')
            return bound_material.attrib['target'][1:]
        except AttributeError:
            return None


