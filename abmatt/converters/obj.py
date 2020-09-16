import math
import os
import re

import numpy as np

from abmatt.converters.convert_lib import PointCollection


class ObjMaterial:
    def __init__(self, name):
        self.name = name
        self.ambient_map = None
        self.diffuse_map = None
        self.specular_map = None
        self.specular_highlight_map = None
        self.alpha_map = None
        self.displacement_map = None
        self.ambient_color = (0.5, 0.5, 0.5)
        self.diffuse_color = (0.5, 0.5, 0.5)
        self.specular_color = (0.33, 0.33, 0.33)
        self.specular_highlight = 0
        self.dissolve = 1
        self.optical_density = 1.5
        self.illumination = 2

    def get_maps(self):
        maps = set()
        maps.add(self.ambient_map)
        maps.add(self.diffuse_map)
        maps.add(self.specular_map)
        maps.add(self.specular_highlight_map)
        maps.add(self.alpha_map)
        maps.add(self.displacement_map)
        if None in maps:
            maps.remove(None)
        return maps

    def get_save_str(self):
        s = 'newmtl ' + self.name + '\n\tNs ' + str(self.specular_highlight) + \
            '\n\tNi ' + str(self.optical_density) + '\n\td ' + str(self.dissolve) + \
            '\n\tTr ' + str(1 - self.dissolve) + '\n\tillum ' + str(self.illumination) +\
            '\n\tKa ' + ' '.join([str(x) for x in self.ambient_color]) + \
            '\n\tKd ' + ' '.join([str(x) for x in self.diffuse_color]) + \
            '\n\tKs ' + ' '.join([str(x) for x in self.specular_color])
        if self.ambient_map:
            s += '\n\tmap_Ka ' + self.ambient_map
        if self.diffuse_map:
            s += '\n\tmap_Kd ' + self.diffuse_map
        if self.specular_map:
            s += '\n\tmap_Ks ' + self.specular_map
        if self.specular_highlight_map:
            s += '\n\tmap_Ns ' + self.specular_highlight_map
        if self.alpha_map:
            s += '\n\tmap_d ' + self.alpha_map
        return s + '\n'


class ObjGeometry():
    def __init__(self, name):
        self.name = name
        self.triangles = []
        self.texcoords = self.normals = self.vertices = None
        self.material_name = None
        self.smooth = False

    @staticmethod
    def normalize_indices_group(indices, data):
        minimum = math.inf
        maximum = -math.inf
        for x in indices:
            for ele in x:
                if ele < minimum:
                    minimum = ele
                if ele > maximum:
                    maximum = ele
        ret = np.array(data[minimum:maximum + 1], np.float)
        return ret, indices - minimum

    def normalize(self, vertices, normals, tex_coords):
        triangles = np.array(self.triangles)
        triangles = triangles - 1
        self.triangles = triangles
        self.vertices = PointCollection(*self.normalize_indices_group(triangles[:, :, 0], vertices))
        self.normals = PointCollection(*self.normalize_indices_group(triangles[:, :, 2], normals))
        self.texcoords = PointCollection(*self.normalize_indices_group(triangles[:, :, 1], tex_coords))


class Obj():
    class ObjParseException(BaseException):
        pass

    def __init__(self, filename, read_file=True):
        self.geometries = []
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.materials = {}
        self.images = set()
        self.filename = filename
        if read_file:
            self.mtllib = None
            self.parse_file(filename)
            for geo in self.geometries:
                geo.normalize(self.vertices, self.normals, self.texcoords)
        else:
            dir, name = os.path.split(filename)
            base_name = os.path.splitext(name)[0]
            self.mtllib = base_name + '.mtl'

    def save(self):
        folder, name = os.path.split(self.filename)
        self.save_mtllib(folder)
        self.save_obj()

    def save_mtllib(self, folder):
        s = '# Wavefront MTL exported with abmatt v0.7.0'
        materials = self.materials
        for x in materials:
            s += '\n' + materials[x].get_save_str()
        with open(os.path.join(folder, self.mtllib), 'w') as f:
            f.write(s)

    def save_obj(self):
        s = '# Wavefront OBJ exported with abmatt v0.7.0\n\nmtllib ' + self.mtllib + '\n\n'
        vertex_index = 1
        normal_index = 1
        texcoord_index = 1
        for geometry in self.geometries:
            s += '#\n# object ' + geometry.name + '\n#\n\n'
            vertex_count = len(geometry.vertices)
            for vert in geometry.vertices:
                s += 'v ' + ' '.join(str(x) for x in vert) + '\n'
            s += '# {} vertices\n\n'.format(vertex_count)
            if geometry.normals:
                normal_count = len(geometry.normals)
                for normal in geometry.normals:
                    s += 'vn ' + ' '.join(str(x) for x in normal) + '\n'
                s += '# {} normals\n\n'.format(normal_count)
            else:
                normal_count = 0
            texcoord_count = len(geometry.texcoords)
            for texcoord in geometry.texcoords:
                s += 'vt ' + ' '.join(str(x) for x in texcoord) + '\n'
            s += '# {} texture coordinates\n\n'.format(texcoord_count)
            # now adjust the tri indices
            tris = np.copy(geometry.triangles)
            tris[:, :, 0] = tris[:, :, 0] + vertex_index
            tris[:, :, 1] = tris[:, :, 1] + texcoord_index
            if normal_count:
                tris[:, :, 2] = tris[:, :, 2] + normal_index
            # start the group of indices
            s += 'o {}\ng {}\n'.format(geometry.name, geometry.name)
            s += 'usemtl {}\n'.format(geometry.material_name)
            s += 's off\n' if not geometry.smooth else 's\n'
            for tri in tris:
                s += 'f ' + ' '.join(['/'.join([str(x) for x in fp]) for fp in tri]) + '\n'
            s += '# {} triangles\n\n'.format(len(tris))
            # now increase the indices
            vertex_index += vertex_count
            normal_index += normal_count
            texcoord_index += texcoord_count
        with open(self.filename, 'w') as f:
            f.write(s)

    def parse_words(self, words, geometry):
        start = words.pop(0)
        if start == 'v':
            self.vertices.append([float(x) for x in words])
        elif start == 'vt':
            self.texcoords.append([float(x) for x in words[:2]])
        elif start == 'vn':
            self.normals.append([float(x) for x in words])
        elif start == 'f':
            tri = []
            for x in words:
                t = x.split('/')
                tri.append([int(y) for y in t])
            geometry.triangles.append(tri)
        elif start == 'o' or start == 'g':
            return words[0]
        elif start == 'usemtl':
            geometry.material_name = words[0]
        elif start == 's':
            geometry.smooth = True
        elif start == 'mtllib':
            self.mtllib = words[0]
        else:
            raise self.ObjParseException('Unknown statement {} {}'.format(start, words.join(' ')))

    def parse_mtl_words(self, words, material):
        first = words.pop(0)
        if 'map' in first:
            map = words[-1]
            if first == 'map_Ka':
                material.ambient_map = map
            elif first == 'map_Kd':
                material.diffuse_map = map
            elif first == 'map_Ks':
                material.specular_map = map
            elif first == 'map_Ns':
                material.specular_highlight_map = map
            elif first in ('map_d', 'map_bump'):
                material.alpha_map = map
            self.images.add(map)
        elif first == 'newmtl':
            return words[0]
        elif first == 'Ka':
            material.ambient_color = [float(x) for x in words]
        elif first == 'Kd':
            material.diffuse_color = [float(x) for x in words]
        elif first == 'Ks':
            material.specular_color = [float(x) for x in words]
        elif first == 'Ns':
            material.specular_highlight = float(words[0])
        elif first == 'd':
            material.dissolve = float(words[0])
        elif first == 'Tr':
            material.dissolve = 1 - float(words[0])
        elif first == 'Ni':
            material.optical_density = float(words[0])
        elif first == 'illum':
            material.illumination = int(words[0])
        elif first == 'disp':
            material.displacement_map = words[-1]
            self.images.add(words[-1])

    def parse_mat_lib(self, mat_lib_path):
        material = None
        with open(mat_lib_path) as f:
            data = f.readlines()
            for line in data:
                if len(line) < 2 or line[0] == '#':
                    continue
                words = re.split("\s+", line.rstrip('\n').strip())
                new_mat = self.parse_mtl_words(words, material)
                if new_mat:
                    material = ObjMaterial(new_mat)
                    self.materials[new_mat] = material

    def parse_file(self, filename):
        geometry = None
        with open(filename) as f:
            data = f.readlines()
            for line in data:
                if len(line) < 2 or line[0] == '#':
                    continue
                words = re.split('\s+', line.rstrip('\n').strip())
                new_geo = self.parse_words(words, geometry)
                if new_geo:
                    if not geometry or geometry.name != new_geo:
                        geometry = ObjGeometry(new_geo)
                        self.geometries.append(geometry)
        if self.mtllib:
            self.parse_mat_lib(self.mtllib)
