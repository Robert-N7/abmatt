from datetime import datetime

import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.converters.convert_lib import Geometry, PointCollection, ColorCollection, Material, Controller, scaleMatrix, \
    float_to_str
from abmatt.converters.xml import XML, XMLNode


class ColladaNode:
    def __init__(self, name, attributes=None):
        self.name = name
        self.attributes = attributes
        self.extra = self.matrix = self.controller = None
        self.geometries = []
        self.nodes = []

    def get_matrix(self):
        if not self.matrix:
            self.matrix = np.identity(4)
        return self.matrix


class Dae:
    def __init__(self, filename=None, initial_scene_name=None):
        self.y_up = True
        self.xml = XML(filename) if filename else self.__initialize_xml(self.y_up)
        self.__initialize_libraries(initial_scene_name)

    def write(self, filename):
        root = self.xml.root
        temp = root.children
        non_empty_libraries = [x for x in root.children if x.children]
        root.children = non_empty_libraries
        self.xml.write(filename)
        root.children = temp

    def get_scene(self):
        return [self.decode_node(x) for x in self.scene.children]

    def get_materials(self):
        return [self.decode_material(x) for x in self.materials]

    def get_image_path(self, image_node):
        init = image_node['init_from']
        path = init.text
        if not path:
            path = init.children[0].text
        return path

    def get_images(self):
        images = {}
        for x in self.images:
            name = x.get_name()
            if not name:
                name = x.get_id()
            images[name] = self.get_image_path(x)
        return images

    def get_element_by_id(self, id):
        return self.xml.get_element_by_id(id)

    @staticmethod
    def search_library_by_id(library, id):
        for x in library:
            if x.get_id() == id:
                return x

    def get_referenced_element(self, element, attribute_source):
        return self.get_element_by_id(element.attributes[attribute_source][1:])

    def trace_technique_common(self, element):
        ele = element['technique_common']['accessor']
        data_type = ele['param'].attributes['type']
        return data_type, self.get_referenced_element(ele, 'source')

    def decode_node(self, xml_node):
        node = ColladaNode(xml_node.get_id(), xml_node.attributes)
        for child in xml_node.children:
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
                node.nodes.append(self.decode_node(child))
            elif child.tag == 'scale':
                matrix = node.get_matrix()
                scaleMatrix(matrix, [float(x) for x in child.text.split()])
            elif child.tag == 'rotation':
                AUTO_FIXER.warn('WARN: rotation transformation not supported for {}'.format(node.name))
            elif child.tag == 'transformation':
                matrix = node.get_matrix()
                transform = [float(x) for x in child.text.split()]
                for i in range(len(transform)):
                    matrix[3, i] += transform[i]
        return node

    def add_node(self, node, parent=None):
        if parent is None:
            parent = self.scene
        xml_node = XMLNode('node', id=node.name, name=node.name, parent=parent, xml=self.xml)
        if node.attributes:
            att = node.attributes
            for key in att:
                xml_node.attributes[key] = att[key]
        xml_node.attributes['sid'] = node.name
        if node.matrix is not None:
            matrix_xml = XMLNode('matrix', ' '.join([float_to_str(x) for x in node.matrix.flatten()]), parent=xml_node)
            matrix_xml.attributes['sid'] = 'matrix'
        if node.extra is not None:
            xml_node.add_child(node.extra)
        if node.controller is not None:
            controller_node = XMLNode('instance_controller', parent=xml_node)
            controller_node.attributes['url'] = '#' + self.add_skin_controller(node.controller).get_id()
            self.__bind_material(controller_node, node.controller.geometry.material_name)
        elif node.geometries:
            for geometry in node.geometries:
                geometry_node = XMLNode('instance_geometry', parent=xml_node)
                geometry_node.attributes['url'] = '#' + self.add_geometry(geometry).get_id()
                self.__bind_material(geometry_node, geometry.material_name)
        for n in node.nodes:
            self.add_node(n, xml_node)
        return xml_node

    def decode_controller(self, xml_controller, bind_material=None):
        name = xml_controller.get_id()
        skin = xml_controller['skin']
        ref = self.get_referenced_element(skin, 'source')
        if ref.tag != 'geometry':   # fix for badly formed xml
            ref = self.search_library_by_id(self.geometries, skin.attributes['source'][1:])
        geometry = self.decode_geometry(ref, bind_material)
        bind_shape_matrix = np.array([float(x) for x in skin['bind_shape_matrix'].text.split()], dtype=float).reshape((4, 4))
        joints = skin['joints']
        for input in joints.children:
            semantic = input.attributes['semantic']
            if semantic == 'INV_BIND_MATRIX':
                matrices = self.get_referenced_element(input, 'source')
                data_type, float_arr = self.trace_technique_common(matrices)
                inv_bind_matrices = np.array([float(x) for x in float_arr.text.split()], float)
                inv_bind_matrices.reshape((-1, 4, 4))
        vertex_weights = skin['vertex_weights']
        vertex_weight_count = [float(x) for x in vertex_weights['vcount'].text.split()]
        vertex_weight_indices = np.array([int(x) for x in vertex_weights['v'].text.split()], int)
        vertex_weight_indices = vertex_weight_indices.reshape((-1, 2))
        input_count = 0
        for input in vertex_weights.get_elements_by_tag('input'):
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
        return Controller(name, bind_shape_matrix, inv_bind_matrices, joint_names, weights, vertex_weight_count,
                          vertex_weight_indices, geometry)

    def add_skin_controller(self, controller):
        controller_id = controller.name + '-controller'
        xml_controller = XMLNode('controller', id=controller_id, parent=self.controllers, xml=self.xml)
        xml_skin = XMLNode('skin', parent=xml_controller)
        xml_skin.attributes['source'] = '#' + self.add_geometry(controller.geometry).get_id()
        bind_shape_matrix = XMLNode('bind_shape_matrix', ' '.join([float_to_str(x) for \
                                                                   x in controller.bind_shape_matrix.flatten()]),
                                    parent=xml_skin)
        joint_source_id = controller_id + '-joints'
        joint_source = XMLNode('source', id=joint_source_id, parent=xml_skin, xml=self.xml)
        name_array_id = joint_source_id + '-array'
        name_array = XMLNode('Name_array', ' '.join(controller.bones), id=name_array_id,
                             parent=joint_source, xml=self.xml)
        bone_len = len(controller.bones)
        name_array.attributes['count'] = str(bone_len)
        self.__create_technique_common(name_array_id, bone_len, 'name', joint_source)
        matrices_source_id = controller_id + '-matrices'
        matrices_source = XMLNode('source', id=matrices_source_id, parent=xml_skin, xml=self.xml)
        matrices_array_id = matrices_source_id + '-array'
        inv_bind_matrix = controller.inv_bind_matrix.flatten()
        float_array = XMLNode('float_array', ' '.join([float_to_str(x) for x in inv_bind_matrix]), id=matrices_array_id,
                              parent=matrices_source, xml=self.xml)
        float_array.attributes['count'] = 16 * bone_len
        self.__create_technique_common(matrices_array_id, bone_len, 'float4x4', matrices_source, 16)
        weight_source_id = controller_id + '-weights'
        weight_source = XMLNode('source', ' '.join([float_to_str(x) for x in controller.weights.flatten()]), id=weight_source_id,
                                parent=xml_skin, xml=self.xml)
        float_array_id = weight_source_id + '-array'
        float_array = XMLNode('float_array', ' '.join([float_to_str(x) for x in controller.weights.flatten()]),
                              id=float_array_id, parent=weight_source, xml=self.xml)
        weight_count = len(controller.weights)
        float_array.attributes['count'] = str(weight_count)  # todo, vertex count or total weight?
        self.__create_technique_common(float_array_id, weight_count, 'float', weight_source)
        joints = XMLNode('joints', parent=xml_skin)
        self.__create_input_node('JOINT', joint_source_id, parent=joints)
        self.__create_input_node('INV_BIND_MATRIX', matrices_source_id, parent=joints)
        vertex_weights = XMLNode('vertex_weights', parent=xml_skin)
        vertex_weights.attributes['count'] = str(len(controller.vertex_weight_indices))
        self.__create_input_node('JOINT', joint_source_id, 0, vertex_weights)
        self.__create_input_node('WEIGHT', weight_source_id, 1, vertex_weights)
        vcount = XMLNode('vcount', ' '.join([str(x) for x in controller.vertex_weight_counts]), parent=vertex_weights)
        vw_data = XMLNode('v', ' '.join([str(x) for x in controller.vertex_weight_indices.flatten()]),
                          parent=vertex_weights)
        return xml_controller

    def decode_geometry(self, xml_geometry, material_name=None):
        mesh = xml_geometry['mesh']
        tri_node = mesh['triangles']
        if not material_name:
            material_name = tri_node.attributes['material']
        inputs = tri_node.get_elements_by_tag('input')
        stride = 0
        indices = [int(x) for x in tri_node['p'].text.split()]
        triangles = np.array(indices, np.uint16).reshape((-1, 3, len(inputs)))
        vertices = normals = colors = None
        texcoords = []
        data_inputs = []
        data_types = []
        offsets = []
        for input in inputs:
            offset = int(input.attributes['offset'])
            source = self.get_referenced_element(input, 'source')
            if source.tag != 'source':
                for x in source.get_elements_by_tag('input'):
                    source = self.get_referenced_element(x, 'source')
                    data_inputs.append(self.__decode_source(source))
                    data_types.append(x.attributes['semantic'])
                    offsets.append(offset)
                    stride += 1
            else:
                data_inputs.append(self.__decode_source(source))
                data_types.append(input.attributes['semantic'])
                offsets.append(offset)
                stride += 1
        new_tris = []
        for i in range(len(data_inputs)):
            decode_type = data_types[i]
            face_indices = np.copy(triangles[:, :, offsets[i]])
            new_tris.append(face_indices)
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
        triangles = np.stack(new_tris, -1)
        name = xml_geometry.get_name()
        if not name:
            name = xml_geometry.get_id()
        geometry = Geometry(name, material_name, triangles=triangles, vertices=vertices,
                            normals=normals, texcoords=texcoords, colors=colors)
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
        geo_xml = XMLNode('geometry', id=name + '-lib', name=name, parent=self.geometries, xml=self.xml)
        mesh = XMLNode('mesh', parent=geo_xml)
        offset = 0
        tris = [vertices.face_indices]
        triangles = XMLNode('triangles')
        triangles.attributes['material'] = material_name
        triangles.attributes['count'] = len(tris[0])
        source_name = name + '-POSITION'
        mesh.add_child(self.__create_source(source_name, vertices.points, ('X', 'Y', 'Z')))
        triangles.add_child(self.__create_input_node('VERTEX', name + '-VERTEX', offset))
        offset += 1
        if normals:
            source_name = name + '-NORMAL0'
            mesh.add_child(self.__create_source(source_name, normals.points, ('X', 'Y', 'Z')))
            triangles.add_child(self.__create_input_node('NORMAL', source_name, offset))
            tris.append(normals.face_indices)
            offset += 1
        if colors:
            source_name = name + '-COLOR'
            mesh.add_child(self.__create_source(source_name, colors.denormalize(), ('R', 'G', 'B', 'A')))
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
        tri_data = XMLNode('p', ' '.join([str(x) for x in data]), parent=triangles)
        vert_node = XMLNode('vertices', id=name + '-VERTEX', parent=mesh, xml=self.xml)
        input_node = self.__create_input_node('POSITION', name + '-POSITION')
        vert_node.add_child(input_node)
        mesh.add_child(triangles)
        return geo_xml

    @staticmethod
    def get_element_by_sid(sid, containing_element):
        for x in containing_element:
            if x.attributes['sid'] == sid:
                return x

    def decode_material(self, material_xml):
        effect = self.get_referenced_element(material_xml['instance_effect'], 'url')
        profile_common = effect['profile_COMMON']
        shader = profile_common['technique'].children[0]
        diffuse = self.__try_get_texture(shader['diffuse'], profile_common)
        ambient = self.__try_get_texture(shader['ambient'], profile_common)
        specular = self.__try_get_texture(shader['specular'], profile_common)
        transparency = 0
        transparency_node = shader['transparency']
        if transparency_node:
            transparency = float(transparency_node['float'].text)
        material = Material(material_xml.attributes['id'], diffuse, ambient, specular, transparency)
        return material

    def add_image(self, name, path):
        image = XMLNode('image', id=name + '-image', name=name, parent=self.images, xml=self.xml)
        init_from = XMLNode('init_from', path, parent=image)
        return image

    def __add_sampler(self, profile_common, name, samplers, swrap='WRAP', twrap='WRAP', minfilter='LINEAR_MIPMAP_LINEAR'):
        if name is None or name in samplers:
            return
        surface_name = name + '-surface'
        new_param = XMLNode('newparam', parent=profile_common)
        new_param.attributes['sid'] = surface_name
        surface = XMLNode('surface', parent=new_param)
        surface.attributes['type'] = '2D'
        image_id = name + '-image'
        init_from = XMLNode('init_from', image_id, parent=surface)
        new_param = XMLNode('newparam', parent=profile_common)
        new_param.attributes['sid'] = name + '-sampler'
        sampler2d = XMLNode('sampler2D', parent=new_param)
        source = XMLNode('source', surface_name, parent=sampler2d)
        samplers.add(name)

    def add_material(self, material):
        transparency = material.transparency
        name = material.name
        material_node = XMLNode('material', parent=self.materials, id=name, name=name, xml=self.xml)
        effect_id = name + '-fx'
        instance_effect = XMLNode('instance_effect')
        material_node.add_child(instance_effect)
        instance_effect.attributes['url'] = '#' + effect_id
        effect = XMLNode('effect', id=effect_id, name=name, parent=self.effects, xml=self.xml)
        profile_common = XMLNode('profile_COMMON', parent=effect)
        technique = XMLNode('technique')
        technique.attributes['sid'] = 'COMMON'
        shader = XMLNode('phong', parent=technique)
        shader.add_child(self.__get_default_shader_color('emission'))
        i = 0
        maps = set()
        i += self.__add_shader_map(shader, 'diffuse', material.diffuse_map, i)
        self.__add_sampler(profile_common, material.diffuse_map, maps)
        i += self.__add_shader_map(shader, 'ambient', material.ambient_map, i)
        self.__add_sampler(profile_common, material.ambient_map, maps)
        self.__add_shader_map(shader, 'specular', material.specular_map, i)
        self.__add_sampler(profile_common, material.specular_map, maps)
        shader.add_child(self.__get_default_shader_float('shininess', 1.071773))
        shader.add_child(self.__get_default_shader_color('reflective'))
        shader.add_child(self.__get_default_shader_float('reflectivity', 1.0))
        node = self.__get_default_shader_color('transparent', (1.0, 1.0, 1.0, 1.0))
        node.attributes['opaque'] = 'RGB_ZERO'
        profile_common.add_child(technique)
        shader.add_child(node)
        shader.add_child(self.__get_default_shader_float('transparency', transparency))
        return material_node

    def __initialize_libraries(self, initial_name):
        libraries = ('images', 'materials', 'effects',
                     'geometries', 'controllers', 'visual_scenes')
        root = self.xml.root
        root_children = root.children
        lib_str = 'library_'
        start = len(lib_str)
        for library in root_children:
            tag = library.tag
            if tag.startswith(lib_str):
                self.__setattr__(tag[start:], library)
            elif tag == 'asset':
                up_axis = library['up_axis']
                if up_axis:
                    self.y_up = True if up_axis.text == 'Y_UP' else False
        for library in libraries:
            if not hasattr(self, library):
                node = XMLNode('library_' + library)
                root_children.append(node)
                self.__setattr__(library, node)
        if initial_name:
            scene_id = initial_name + '-scene'
            self.scene = XMLNode('visual_scene', id=scene_id, name=initial_name, parent=self.visual_scenes)
            scene = XMLNode('scene', parent=root)
            instance_scene = XMLNode('instance_visual_scene', parent=scene)
            instance_scene.attributes['url'] = '#' + scene_id
        else:
            self.scene = self.get_referenced_element(self.xml.root['scene']['instance_visual_scene'], 'url')

    @staticmethod
    def __initialize_assets(root, y_up):
        asset = XMLNode('asset', parent=root)
        contributor = XMLNode('contributor', parent=asset)
        authoring_tool = XMLNode('authoring_tool', 'abmatt COLLADA exporter', parent=contributor)
        time_stamp = datetime.now()
        created = XMLNode('created', time_stamp, parent=asset)
        modified = XMLNode('modified', time_stamp, parent=asset)
        up = 'Y_UP' if y_up else 'Z_UP'
        up_axis = XMLNode('up_axis', up, parent=asset)

    @staticmethod
    def __initialize_xml(y_up):
        xml = XML()
        root = XMLNode('COLLADA')
        root.attributes['xmlns'] = 'http://www.collada.org/2005/11/COLLADASchema'
        root.attributes['version'] = '1.4.1'
        Dae.__initialize_assets(root, y_up)
        xml.root = root
        return xml

    @staticmethod
    def __get_default_shader_color(name, iterable=(0.0, 0.0, 0.0, 1.0)):
        shader_color = XMLNode(name)
        text = ' '.join([float_to_str(x) for x in iterable])
        color = XMLNode('color', text)
        color.attributes['sid'] = name
        shader_color.add_child(color)
        return shader_color

    @staticmethod
    def __get_default_shader_float(name, fl=0.0):
        node = XMLNode(name)
        fl = XMLNode('float', float_to_str(fl), parent=node)
        fl.attributes['sid'] = name
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
        accessor.attributes['source'] = '#' + name + '-array'
        point_len = len(data_collection)
        accessor.attributes['count'] = point_len
        stride = len(data_collection[0])
        accessor.attributes['stride'] = stride
        for letter in params:
            param = XMLNode('param', name=letter, parent=accessor)
            param.attributes['type'] = 'float'
        source_array.attributes['count'] = stride * point_len
        return source

    @staticmethod
    def __create_input_node(semantic, source, offset=None, parent=None):
        node = XMLNode('input', parent=parent)
        node.attributes['semantic'] = semantic
        if offset is not None:
            node.attributes['offset'] = str(offset)
        node.attributes['source'] = '#' + source
        return node

    def __decode_input(self, input, triangles):
        decoded_type = input.attributes['semantic']
        source = self.get_referenced_element(input, 'source')
        while source.tag != 'source':
            source = self.get_referenced_element(source['input'], 'source')
        accessor = source['technique_common']['accessor']
        stride = accessor.attributes['stride']
        float_array = self.get_referenced_element(accessor, 'source')
        points = np.array([float(x) for x in float_array.text.split()])
        if stride:
            points = points.reshape((-1, int(stride)))
        offset = int(input.attributes['offset'])
        if decoded_type == 'COLOR':
            return decoded_type, ColorCollection(points, triangles[:, :, offset], normalize=True)
        elif decoded_type in ('VERTEX', 'NORMAL', 'TEXCOORD'):
            return decoded_type, PointCollection(points, triangles[:, :, offset])
        else:
            raise ValueError('Unknown collada input {}'.format(decoded_type))

    def __decode_source(self, source):
        data = np.array([float(x) for x in source['float_array'].text.split()], dtype=float)
        accessor = source['technique_common']['accessor']
        stride = accessor.attributes.get('stride')
        if stride:
            data = data.reshape((-1, int(stride)))
        return data

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

    @staticmethod
    def __bind_material(node, material_name):
        bind_mat = XMLNode('bind_material', parent=node)
        tech_common = XMLNode('technique_common', parent=bind_mat)
        instance_mat = XMLNode('instance_material', parent=tech_common)
        instance_mat.attributes['symbol'] = material_name
        instance_mat.attributes['target'] = '#' + material_name
        return bind_mat

    @staticmethod
    def __add_shader_map(shader, map_type='diffuse', map=None, texcoord=0):
        if map is None:
            map = (0.3, 0.3, 0.3, 1)
        if type(map) == tuple:
            shader.add_child(Dae.__get_default_shader_color(map_type, map))
            return False
        else:
            map_node = XMLNode(map_type, parent=shader)
            tex_node = XMLNode('texture', parent=map_node)
            tex = map + '-sampler'
            tex_node.attributes['texture'] = tex
            tex_node.attributes['texcoord'] = 'CHANNEL' + str(texcoord)
            return True

    def __try_get_texture(self, map_xml_node, profile_common):
        if map_xml_node is None:
            return map_xml_node
        texture = map_xml_node['texture']
        if texture:
            id = texture.attributes['texture']
            image = self.get_element_by_id(id)
            if not image:
                sampler = self.get_element_by_sid(id, profile_common)
                surface_id = sampler['sampler2D']['source'].text
                surface_param = self.get_element_by_sid(surface_id, profile_common)
                init_from = surface_param['surface']['init_from']
                image_id = init_from.text
                if not image_id:
                    image_id = init_from.children[0].text
                image = self.get_element_by_id(image_id)
            init_from = image['init_from']
            image_path = init_from.text
            if not image_path:
                image_path = init_from.children[0].text
            return image_path

    @staticmethod
    def __get_bound_material(node):
        bound_material = node['bind_material']['technique_common']['instance_material']
        return bound_material.attributes['target'][1:]

