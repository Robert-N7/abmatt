import os
import shutil
from copy import copy
from struct import unpack_from

from abmatt import converters
from abmatt.brres import Brres
from abmatt.brres.lib import matching
from abmatt.brres.mdl0.normal import Normal
from abmatt.brres.mdl0.vertex import Vertex
from abmatt.converters.convert_dae import DaeConverter
from abmatt.converters.encoder import GeometryEncoder, PointEncoder, ModelEncoder, ColorEncoder
from abmatt.brres.mdl0.polygon import Polygon
from abmatt.brres.mdl0.bone import Bone
from abmatt.converters.geometry import get_stride


def create_mirror(brres_file_name, working_folder='tmp'):
    """Creates a mirror of the brres file by decoding and re-encoding the file
    :returns (original_brres, new_brres)
    """
    original = Brres(brres_file_name)
    base_name = os.path.splitext(os.path.basename(brres_file_name))[0]
    dae_file = os.path.join(working_folder, base_name + '.dae')
    DaeConverter(original, mdl_file=dae_file, encode=False).convert()
    new_file_name = os.path.join(working_folder, base_name + '.brres')
    shutil.copyfile(brres_file_name, new_file_name)
    new_brres = Brres(new_file_name)
    DaeConverter(new_brres, mdl_file=dae_file, encode=True, encoder=MirrorEncoder(original.models[0])).convert()
    new_brres.save(overwrite=True)
    return original, new_brres


class MirrorEncoder(ModelEncoder):
    """Mirrors a model encoding"""

    def __init__(self, mdl0, geo_name_mapping=None):
        """
        :param mdl0: existing model
        :param geo_name_mapping: How to map the incoming geometry names to the polygons, the default is to match names
        """
        self.geo_name_mapping = geo_name_mapping
        self.mdl0 = mdl0

    def before_encoding(self, geometries):
        self.__mirror_colors(geometries)

    def __mirror_colors(self, geometries):
        # We get the primary colors to use here
        used_colors = {}
        # and here we store the mapping of geometries that need to combine their colors to the original
        remap_geo_color = {}
        for x in self.mdl0.objects:
            color = x.get_color_group()
            if color:
                if color.name in used_colors:
                    remap_geo_color[x.name] = used_colors[color.name]
                else:
                    used_colors[color.name] = x.name
        # map the goemetries to their colors
        geo_to_color = {}
        for x in geometries:
            geo_to_color[x.name] = x.colors
        # and now combine the colors that need remapping
        for x in geometries:
            if x.name in remap_geo_color and x.colors:
                color = geo_to_color.get(remap_geo_color[x.name])
                if color is not None:
                    color.combine(x.colors)

    def after_encode(self, new_mdl0):
        new_mdl0.rebuild_header()
        new_mdl0.minimum = [x for x in self.mdl0.minimum]
        new_mdl0.maximum = [x for x in self.mdl0.maximum]
        self.after_encode_bones(self.mdl0.bones[0], new_mdl0.bones[0])
        self.reorder_group(new_mdl0.vertices, self.mdl0.vertices)
        self.reorder_group(new_mdl0.normals, self.mdl0.normals)
        self.reorder_group(new_mdl0.uvs, self.mdl0.uvs)
        self.reorder_group(new_mdl0.colors, self.mdl0.colors)
        # self.process_polys(new_mdl0.objects, self.mdl0.objects)
        self.reorder_anims(new_mdl0.srt0_collection, self.mdl0.srt0_collection)
        self.reorder_anims(new_mdl0.pat0_collection, self.mdl0.pat0_collection)

    def process_polys(self, new_polys, old_polys):
        """Expects polys to be in order"""
        assert len(new_polys) == len(old_polys)
        for i in range(len(new_polys)):
            x = new_polys[i]
            y = old_polys[i]
            x.normal_index = y.normal_index
            x.color0_index = y.color0_index
            x.uv_indices = copy(y.uv_indices)
            x.weight_index = y.weight_index
            x.face_count = y.face_count
            x.facepoint_count = y.facepoint_count
            x.data = copy(y.data)
            if i == 0:
                self.recode_data(x, y)

    def recode_data(self, new_poly, old_polygon):
        tri_strips, tris, r = self.decode_data(old_polygon)
        tri_strips.reverse()    # reverse the tri strip order
        tri_strips.extend(tris)
        new_poly.data = bytearray(b''.join(tri_strips))
        new_poly.data.extend(r)
        assert len(new_poly.data) % 0x20 == 0

    def decode_data(self, polygon):
        data = polygon.data
        encode_str = polygon.encode_str
        stride = get_stride(encode_str)
        tri_strips = []
        tris = []
        total_fp = 0
        i = 0
        last_fp_count = 600000
        while i < len(data) and total_fp < polygon.facepoint_count:
            x = data[i]
            start = i
            [num_facepoints] = unpack_from('>H', data, i + 1)
            i += 3
            if x == 0x98:
                end = i+num_facepoints * stride
                tri_strips.append(data[start:end])
            elif x == 0x90:
                end = i+num_facepoints*stride
                tris.append(data[start:end])
            else:
                raise ValueError('Unknown')
            i = end
            total_fp += num_facepoints
        remaining = data[i:]
        return tri_strips, tris, remaining

    @staticmethod
    def reorder_group(group, old_group):
        tmp = [x for x in group]
        group.clear()
        for x in old_group:
            for y in tmp:
                if y.name == x.name:
                    group.append(y)
                    tmp.remove(y)
                    break
        for x in tmp:
            group.append(x)

    @staticmethod
    def reorder_anims(anim_collection, original):
        if anim_collection is None or original is None or len(anim_collection) <= 1:
            return
        anims = [x for x in anim_collection]
        for x in anims:
            anim_collection.remove(x)
        to_remove = []
        for x in original:
            for y in anims:
                if x == y:
                    to_remove.append(y)
                    anim_collection.add(y)
                    break
        for x in to_remove:
            anims.remove(x)
        for x in anims:
            anim_collection.add(x)

    @staticmethod
    def after_encode_bones(old_bone, new_bone):
        new_bone.scale = old_bone.scale
        new_bone.rotation = old_bone.rotation
        new_bone.translation = old_bone.translation
        new_bone.transform_matrix = old_bone.transform_matrix
        new_bone.inverse_matrix = old_bone.inverse_matrix

    def get_encoder(self, geometry):
        if self.geo_name_mapping is not None:
            match = self.geo_name_mapping.get(geometry.name)
        else:
            match = matching.fuzzy_match(geometry.name, self.mdl0.objects)
        return MirrorGeometryEncoder(match) if match else None


class MirrorGeometryEncoder(GeometryEncoder):
    """Mirrors the formats of an existing polygon"""

    def __init__(self, polygon):
        """
        :param polygon: An mdl0 polygon to mirror
        :type polygon: Polygon
        """
        super().__init__()
        self.mirror_geo = polygon
        self.vertex_encoder = MirrorPointEncoder(polygon.vertices)
        self.normal_encoder = MirrorPointEncoder(polygon.normals) if polygon.normals else None
        if polygon.uv_count > 0:
            self.uv_encoders = [MirrorPointEncoder(x) for x in polygon.uvs]
        if polygon.color_count > 0:
            self.color_encoder = MirrorColorEncoder(polygon.get_color_group())

    def after_encode(self, encoded_poly):
        results = matching.Matching.match_group_full_sensitive(self.mirror_geo.name, encoded_poly.parent.objects, [])
        if not results:
            encoded_poly.name = self.mirror_geo.name


class MirrorColorEncoder(ColorEncoder):
    def after_encode(self, mdl0_color):
        results = matching.Matching.match_group_full_sensitive(self.color.name, mdl0_color.parent.colors, [])
        if not results:
            mdl0_color.name = self.color.name

    def should_consolidate(self):
        return False

    def get_format(self):
        return self.color.format

    def __init__(self, color):
        self.color = color


class MirrorPointEncoder(PointEncoder):
    def __init__(self, point):
        self.point = point

    def after_encode(self, mdl0_point):
        if type(mdl0_point) == Vertex:
            group = mdl0_point.parent.vertices
        elif type(mdl0_point) == Normal:
            group = mdl0_point.parent.normals
        else:
            group = mdl0_point.parent.uvs
        results = matching.Matching.match_group_full_sensitive(self.point.name, group, [])
        if not results:
            mdl0_point.name = self.point.name

    def get_format(self):
        return self.point.format_str

    def get_divisor(self):
        return self.point.divisor

    def should_consolidate(self):
        return False  # Preserve structure
