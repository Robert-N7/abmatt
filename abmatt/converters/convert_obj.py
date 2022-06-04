import math
import os
import sys
import time
from math import dist

import numpy as np

from abmatt.autofix import AutoFix
from abmatt.converters.arg_parse import cmdline_convert
from abmatt.converters.convert_lib import Converter
from abmatt.converters.geometry import Geometry
from abmatt.converters.material import Material
from abmatt.converters.obj import Obj, ObjGeometry, ObjMaterial
from brres import Brres
from converters.colors import ColorCollection
from converters.points import PointCollection


class ObjConverter(Converter):

    def __collect_geometries(self, obj_geometries, bone):
        material_geometry_map = {}
        # first collect geometries
        for geometry in obj_geometries:
            if self._should_include_geometry(geometry):
                normals = None if self.NO_NORMALS & self.flags else geometry.normals
                texcoords = [geometry.texcoords] if geometry.has_texcoords else None
                geo = Geometry(geometry.name, geometry.material_name, geometry.vertices, texcoords, normals,
                               triangles=geometry.triangles, linked_bone=bone)
                # geo.encode(self.mdl0)
                mat = geometry.material_name
                if mat in material_geometry_map:
                    material_geometry_map[mat].combine(geo)
                else:
                    material_geometry_map[mat] = geo
                    self.geometries.append(geo)
        return material_geometry_map

    def load_model(self, model_name=None):
        mdl = self._start_loading(model_name)
        bone = mdl.add_bone(mdl.name)
        self.obj = obj = Obj(self.mdl_file)
        self.material_geometry_map = material_geometry_map = self.__collect_geometries(obj.geometries, bone)
        self._before_encoding()
        for material in material_geometry_map:
            super()._encode_geometry(material_geometry_map[material])
        self.import_textures_map = self.__convert_set_to_map(obj.images)
        return self._end_loading()

    def encode_materials(self):
        for material in self.material_geometry_map:
            try:
                self.__encode_material(self.obj.materials[material])
            except KeyError:
                self._encode_material(Material(material))

    def save_model(self, mdl0=None):
        base_name, mdl0 = self._start_saving(mdl0)
        polygons = self.polygons
        obj = Obj(self.mdl_file, False)
        obj_materials = obj.materials
        for mat in self.materials:
            obj_mat = self.__decode_material(mat)
            obj_materials[obj_mat.name] = obj_mat
        obj_geometries = obj.geometries
        has_colors = False
        for x in polygons:
            geometry = super()._decode_geometry(x)
            if geometry:
                material = geometry.material_name
                obj_geometries.append(self.__decode_geometry(geometry, material))
                if x.get_color_group():
                    has_colors = True
        if has_colors:
            AutoFix.warn('Loss of color data exporting obj')
        self._end_saving(obj)

    @staticmethod
    def __convert_map_to_layer(material, map):
        base_name = os.path.splitext(os.path.basename(map))[0]
        if not material.getLayerByName(base_name):
            return material.add_layer(base_name)

    def __convert_set_to_map(self, obj_images):
        path_map = {}
        for x in obj_images:
            path_map[os.path.splitext(os.path.basename(x))[0]] = x
        return path_map

    def __encode_material(self, obj_mat):
        return self._encode_material(Material(obj_mat.name, obj_mat.diffuse_map, obj_mat.ambient_map,
                                              obj_mat.specular_map, obj_mat.get_transparency()))

    @staticmethod
    def __decode_geometry(geometry, material_name):
        geo = ObjGeometry(geometry.name)
        geo.vertices = geometry.apply_linked_bone_bindings()
        geo.material_name = material_name
        geo.vertices = geometry.vertices
        geo.normals = geometry.normals
        geo.has_normals = bool(geo.normals)
        texcoords = geometry.texcoords
        if len(texcoords) > 1:
            AutoFix.warn('Loss of UV data for {}.'.format(geo.name))
        stack = [geo.vertices.face_indices]
        if len(texcoords):
            geo.texcoords = texcoords[0]
            stack.append(geo.texcoords.face_indices)
            geo.has_texcoords = True
        else:
            geo.texcoords = None
            geo.has_texcoords = False
        if geo.normals:
            stack.append(geo.normals.face_indices)
        geo.triangles = np.stack(stack, -1)
        return geo

    def __decode_material(self, material):
        mat = ObjMaterial(material.name)
        if material.xlu:
            mat.dissolve = 0.5
        first = True
        for layer in material.layers:
            name = layer.name
            if name not in self.tex0_map:
                tex = self.texture_library.get(name)
                if tex:
                    self.tex0_map[name] = tex
                else:
                    AutoFix.warn('No texture found matching {}'.format(name))
            if first:
                path = os.path.join(self.image_dir, name + '.png')
                mat.diffuse_map = path
                mat.ambient_map = path
            first = False
        return mat


def __load_vert_color(vert_color, geo, vertices):
    points = np.around(geo.vertices.points, 3)
    for tri in points[geo.vertices.face_indices]:
        for i, vert in enumerate(tri):
            t_vert = tuple(vert)
            if t_vert not in vertices:
                vertices[t_vert] = [(
                    vert_color,
                    tri[i - 2],
                    math.dist(tri[i - 2], t_vert),
                    tri[i - 1],
                    math.dist(tri[i - 1], t_vert)
                )]
            else:
                vertices[t_vert].append((
                    vert_color,
                    tri[i - 2],
                    math.dist(tri[i - 2], t_vert),
                    tri[i - 1],
                    math.dist(tri[i - 1], t_vert)
                ))


def __get_best_tri(vert, tp1, tp2, possible):
    total_1 = math.dist(tp1, vert)
    total_2 = math.dist(tp2, vert)
    for i, x in enumerate(possible):
        if np.allclose(math.dist(tp1, x[1]) + x[2], total_1) and \
                np.allclose(math.dist(tp2, x[3]) + x[4], total_2):
            color = possible.pop(i)
            return color[0]
    return possible[0][0]


def __apply_colors_to_geo(colors, geo, default_color):
    decoded = geo.get_decoded()
    points = np.around(decoded.vertices.points, 3)
    new_colors = {}
    new_colors_arr = []
    fp = []
    failed = 0
    for tri in points[decoded.vertices.face_indices]:
        fp_row = []
        for i, vert in enumerate(tri):
            t_vert = tuple(vert)
            possible = colors.get(t_vert)
            if not possible:
                failed += 1
                color = default_color
            elif len(possible) == 1:
                color = possible[0][0]
            else:
                color = __get_best_tri(vert, tri[i - 2], tri[i - 1], possible)
            t = tuple(color)
            index = new_colors.get(t)
            if index is None:
                new_colors[t] = index = len(new_colors_arr)
                new_colors_arr.append(t)
            fp_row.append(index)
        fp.append(fp_row)
    decoded.colors = ColorCollection(np.array(new_colors_arr), np.array(fp), normalize=True)
    if failed:
        AutoFix.warn(f'Failed to find vertices and used default color {failed} times.')
    return failed


def obj_mats_to_vertex_colors(polygons, obj, default_color=None, overwrite=False):
    start = time.time()
    AutoFix.info(f'Creating vertex colors from {obj}...', 3)
    default_color_amount = 0
    if not overwrite:
        polygons = [x for x in polygons if not x.get_decoded().colors]
    if not polygons:
        return default_color_amount
    if not default_color:
        default_color = (0.5, 0.5, 0.5, 1)
    if type(obj) is not Obj:
        obj = Obj(obj)
    # Gather up color corresponding to each material
    mat_to_vert_color = {}
    for material in obj.materials.values():
        vertex_color = [x for x in material.diffuse_color]
        vertex_color.append(material.dissolve)
        mat_to_vert_color[material.name] = vertex_color

    named = {x.name for x in polygons}
    geom_vertices = {'': {}}
    for geom in obj.geometries:
        name = geom.name.split('-')[0]
        if name in named:
            if name not in geom_vertices:
                geom_vertices[name] = {}
            __load_vert_color(
                mat_to_vert_color.get(geom.material_name), geom, geom_vertices[name]
            )
        else:
            __load_vert_color(
                mat_to_vert_color.get(geom.material_name), geom, geom_vertices['']
            )
    for x in polygons:
        vertices = geom_vertices[x.name] if x.name in geom_vertices else geom_vertices['']
        default_color_amount += __apply_colors_to_geo(vertices, x, default_color)
        x.get_decoded().recode(x)
    AutoFix.info(f'... Finished in {round(time.time() - start, 2)} secs.', 3)
    return default_color_amount


def __get_color_map(poly):
    poly.apply_linked_bone_bindings()
    colors = poly.colors
    o_points = poly.vertices.points
    color_map = {}
    # Create triangle for each vertex
    for i, tri in enumerate(poly.vertices.face_indices):
        tri_verts = o_points[tri]
        color = colors.rgba_colors[colors.face_indices[i]]
        t1 = tuple(color[0])
        t2 = tuple(color[1])
        t3 = tuple(color[2])
        if t1 not in color_map:
            color_map[t1] = []
        if t2 not in color_map:
            color_map[t2] = []
        if t3 not in color_map:
            color_map[t3] = []
        color_map[t1].append((
            tri_verts[0],
            tri_verts[0] + (tri_verts[1] - tri_verts[0]) / 5,
            tri_verts[0] + (tri_verts[2] - tri_verts[0]) / 5
        ))
        color_map[tuple(color[1])].append((
            tri_verts[1],
            tri_verts[1] + (tri_verts[2] - tri_verts[1]) / 5,
            tri_verts[1] + (tri_verts[0] - tri_verts[1]) / 5
        ))
        color_map[tuple(color[2])].append((
            tri_verts[2],
            tri_verts[2] + (tri_verts[0] - tri_verts[2]) / 5,
            tri_verts[2] + (tri_verts[1] - tri_verts[2]) / 5
        ))
    return color_map


def vertex_colors_to_obj(polygons, obj):
    if not isinstance(obj, Obj):
        obj = Obj(obj, read_file=False)
    AutoFix.info('Exporting vertex colors...', 3)
    start = time.time()
    # Strategy: create 3 small triangles from each triangle,
    # each corresponding to a vertex color. We'll create a
    # geometry and material consisting of all small triangles
    # for each vertex color.
    for poly in [x for x in polygons if x.has_color0()]:
        color_map = __get_color_map(poly.get_decoded())
        for color, tris in color_map.items():
            geo = ObjGeometry(f'{poly.name}-{"_".join([str(x) for x in color])}')
            points = np.array(tris).reshape(-1, 3)
            geo.vertices = PointCollection(points, np.arange(len(points)).reshape(-1, 3))
            geo.vertices.consolidate_points()
            geo.material_name = geo.name
            geo.texcoords = PointCollection(
                np.array([[0, 0], [0, 1], [1, 1]]),
                np.array([i for i in range(3)] * len(tris)).reshape(-1, 3)
            )
            geo.has_texcoords = True
            geo.has_normals = False
            geo.triangles = np.stack([geo.vertices.face_indices, geo.texcoords.face_indices], -1)
            obj.geometries.append(geo)
            obj.materials[geo.name] = ObjMaterial(
                geo.name, dissolve=color[-1] / 255.0, diffuse_color=[x / 255.0 for x in color[:3]]
            )
    obj.save()
    AutoFix.info(f'... Finished in {round(time.time() - start, 2)} secs.', 3)


def main():
    cmdline_convert(sys.argv[1:], '.obj', ObjConverter)


if __name__ == '__main__':
    main()
