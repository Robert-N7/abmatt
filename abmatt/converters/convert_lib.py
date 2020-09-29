import math
import os
import time
from struct import pack, unpack, unpack_from

from PIL import Image
import numpy as np

from abmatt.brres.lib.autofix import AUTO_FIXER, Bug
from abmatt.brres.mdl0.color import Color
from abmatt.brres.mdl0.normal import Normal
from abmatt.brres.mdl0.polygon import Polygon
from abmatt.brres.mdl0.texcoord import TexCoord
from abmatt.brres.mdl0.vertex import Vertex
from abmatt.brres.mdl0 import material
from abmatt.brres.tex0 import EncodeError, Tex0, ImgConverter, ImgConverterI, NoImgConverterError
from abmatt.converters.triangle import TriangleSet
from abmatt.converters.matrix import apply_matrix, combine_matrices, matrix_to_srt
from abmatt.brres.mdl0 import Mdl0


class Converter:
    NoNormals = 0x1
    NoColors = 0x2
    IDENTITY_MATRIX = np.identity(4)
    DETECT_FILE_UNITS = True

    class ConvertError(Exception):
        pass

    def _start_loading(self, model_name):
        AUTO_FIXER.info('Converting {}... '.format(self.mdl_file))
        self.start = time.time()
        self.cwd = os.getcwd()
        self.mdl_file = os.path.abspath(self.mdl_file)
        brres_dir, brres_name = os.path.split(self.brres.name)
        base_name = os.path.splitext(brres_name)[0]
        self.is_map = True if 'map' in base_name else False
        dir, name = os.path.split(self.mdl_file)
        material.Material.WARNINGS_ON = False
        if dir:
            os.chdir(dir)  # change to the dir to help find relative paths
        return self._init_mdl0(brres_name, os.path.splitext(name)[0], model_name)

    def _end_loading(self):
        mdl0 = self.mdl0
        mdl0.rebuild_header()
        self.brres.add_mdl0(mdl0)
        if self.is_map:
            mdl0.add_map_bones()
        os.chdir(self.cwd)
        material.Material.WARNINGS_ON = True
        AUTO_FIXER.info('\t... finished in {} secs'.format(round(time.time() - self.start, 2)))
        return mdl0

    def _init_mdl0(self, brres_name, mdl_name, mdl0_name):
        if mdl0_name is None:
            mdl0_name = self.__get_mdl0_name(brres_name, mdl_name)
        self.replacement_model = self.brres.getModel(mdl0_name)
        self.mdl0 = Mdl0(mdl0_name, self.brres)
        return self.mdl0

    @staticmethod
    def __get_mdl0_name(brres_name, model_name):
        common_models = ('course', 'map', 'vrcorn')
        for x in common_models:
            if x in brres_name or x in model_name:
                return x
        model_name = os.path.splitext(model_name)[0]
        replace = brres_name + '-'
        if model_name.startswith(replace) and len(model_name) > len(replace):
            model_name = model_name[len(replace):]
        return model_name

    @staticmethod
    def set_bone_matrix(bone, matrix):
        """Untested set translation/scale/rotation with matrix"""
        bone.transform_matrix = matrix[:3]  # don't include fourth row
        bone.inverse_matrix = np.linalg.inv(matrix)[:3]
        bone.scale, bone.rotation, bone.translation = matrix_to_srt(matrix)

    @staticmethod
    def is_identity_matrix(matrix):
        return np.allclose(matrix, Converter.IDENTITY_MATRIX)

    def _encode_material(self, generic_mat):
        if self.replacement_model:
            m = self.replacement_model.getMaterialByName(generic_mat.name)
            if m:
                mat = material.Material.get_unique_material(generic_mat.name, self.mdl0)
                self.mdl0.add_material(mat)
                mat.paste(m)
            else:
                mat = generic_mat.encode(self.mdl0)
        else:
            mat = generic_mat.encode(self.mdl0)
        for x in mat.layers:
            self.image_library.add(x.name)
        return mat

    @staticmethod
    def __normalize_image_path_map(image_path_map):
        normalized = {}
        for x in image_path_map:
            path = image_path_map[x]
            normalized[os.path.splitext(os.path.basename(path))[0]] = path
        normalized.update(image_path_map)
        return normalized

    def _import_images(self, image_path_map):
        try:
            normalized = False
            for map in self.image_library:  # only add images that are used
                path = image_path_map.get(map)
                if path is None:
                    if not normalized:
                        image_path_map = self.__normalize_image_path_map(image_path_map)
                        path = image_path_map.get(map)
                        normalized = True
                    if path is None:
                        continue
                self._try_import_texture(self.brres, path, map)
        except NoImgConverterError as e:
            AUTO_FIXER.error(e)

    def _try_import_texture(self, brres, image_path, layer_name=None):
        if not layer_name:
            layer_name = os.path.splitext(os.path.basename(image_path))[0]
        if not brres.hasTexture(layer_name):
            if len(image_path) < 4:
                AUTO_FIXER.warn('Image path {} is not valid'.format(image_path))
                return layer_name
            ext = image_path[-4:].lower()
            # check it if it's the first or if a resize occurred or not correct extension
            if self.is_first_image or self.check_image or ext != '.png':
                self.is_first_image = False
                if image_path.startswith('file://'):
                    image_path = image_path.replace('file://', '')
                if not os.path.exists(image_path):
                    return layer_name
                im = Image.open(image_path)
                modified = False
                if ext != '.png':
                    AUTO_FIXER.info(f'Conversion from {ext} to tex0 not supported, converting to png', 4)
                    dir, name = os.path.split(image_path)
                    image_path = os.path.join(dir, os.path.splitext(name)[0] + '.png')
                    modified = True
                width, height = im.size
                if width > Tex0.MAX_IMG_SIZE or height > Tex0.MAX_IMG_SIZE:
                    new_width, new_height = Tex0.get_scaled_size(width, height)
                    b = Bug(2, 2, f'Texture {layer_name} too large ({width}x{height}).',
                            f'Resize to {new_width}x{new_height}.')
                    dir, name = os.path.split(image_path)
                    base, ext = os.path.splitext(name)
                    image_path = os.path.join(dir, base + '-resized' + ext)
                    im = im.resize((width, height), ImgConverterI.get_resample())
                    modified = True
                    self.check_image = True
                    b.resolve()
                if modified:
                    im.save(image_path)
            try:
                brres.import_texture(image_path, layer_name)
            except EncodeError:
                AUTO_FIXER.warn('Failed to encode image {}'.format(image_path))
        return layer_name

    def __init__(self, brres, mdl_file, flags=0):
        self.brres = brres
        self.mdl_file = mdl_file
        self.mdl0 = None
        self.flags = flags
        self.check_image = False
        self.is_first_image = True
        self.image_library = set()
        self.replacement_model = None

    def load_model(self, model_name):
        raise NotImplementedError()

    def save_model(self, mdl0):
        raise NotImplementedError()


def get_index_format(item):
    l = len(item)
    if l > 0xffff:
        raise Converter.ConvertError(f'{item.name} exceeds max length! ({len(item)})')
    elif l > 0xff:
        return Polygon.INDEX_FORMAT_SHORT, 'H'
    else:
        return Polygon.INDEX_FORMAT_BYTE, 'B'


def decode_tri_strip(decoder, decoder_byte_len, data, start_offset, num_facepoints, face_point_indices):
    face_points = []
    flip = False
    for i in range(num_facepoints):
        face_points.append(unpack_from(decoder, data, start_offset))
        start_offset += decoder_byte_len
        if i >= 2:
            if flip:
                face_point_indices.append((face_points[i - 1], face_points[i - 2], face_points[i]))
            else:
                face_point_indices.append(face_points[i - 2:i + 1])
        flip = not flip
    return start_offset


def decode_tris(decoder, decoder_byte_len, data, start_offset, num_facepoints, face_point_indices):
    assert num_facepoints % 3 == 0
    for i in range(int(num_facepoints / 3)):
        tri = []
        for j in range(3):
            tri.append(unpack_from(decoder, data, start_offset))
            start_offset += decoder_byte_len
        face_point_indices.append(tri)
    return start_offset


def decode_geometry_group(geometry):
    arr = np.array(geometry.data, np.float)
    if geometry.divisor:
        arr = arr / (2 ** geometry.divisor)
    return arr


def decode_polygon(polygon):
    """ Decodes an mdl0 polygon
        :returns geometry
    """
    # build the fmt_str decoder
    fmt_str = '>'
    geometry_index = 0
    if polygon.has_pos_matrix:
        fmt_str += 'B'
        pos_matrix_index = geometry_index
        geometry_index += 1
        raise Converter.ConvertError('{} vertex weighting not supported'.format(polygon.name))
    else:
        pos_matrix_index = -1
    tex_matrix_index = -1
    for x in polygon.has_tex_matrix:
        if x:
            fmt_str += 'B'
            if tex_matrix_index < 0:
                tex_matrix_index = geometry_index
            geometry_index += 1
            raise Converter.ConvertError('{} texcoord matrix not supported'.format(polygon.name))
    vertex_index = geometry_index
    geometry_index += 1
    vertices = polygon.get_vertex_group()
    fmt_str += polygon.get_fmt_str(polygon.vertex_index_format)
    normals = polygon.get_normal_group()
    if normals:
        fmt_str += polygon.get_fmt_str(polygon.normal_index_format)
        normal_index = geometry_index
        geometry_index += 1
    else:
        normal_index = -1
    colors = polygon.get_color_group()
    if colors:
        fmt_str += polygon.get_fmt_str(polygon.color0_index_format)
        color_index = geometry_index
        geometry_index += 1
    else:
        color_index = -1
    texcoords = []
    texcoord_index = -1
    for i in range(polygon.num_tex):
        texcoords.append(polygon.get_tex_group(i))
        fmt_str += polygon.get_fmt_str(polygon.tex_index_format[i])
        if i == 0:
            texcoord_index = geometry_index
            geometry_index += 1
    fp_data_length = 0
    for x in fmt_str:
        if x == 'H':
            fp_data_length += 2
        elif x == 'B':
            fp_data_length += 1
        elif x != '>':
            raise ValueError('Unknown decoder format {}'.format(x))
    # now decode the indices
    face_point_indices = []
    data = polygon.vt_data
    total_face_points = i = 0
    bones = []
    face_point_count = polygon.facepoint_count
    while total_face_points < face_point_count:
        [cmd] = unpack_from('>B', data, i)
        i += 1
        if cmd in (0x98, 0x90):
            [num_facepoints] = unpack_from('>H', data, i)
            i += 2
            if cmd == 0x98:
                i = decode_tri_strip(fmt_str, fp_data_length, data, i, num_facepoints, face_point_indices)
            elif cmd == 0x90:
                i = decode_tris(fmt_str, fp_data_length, data, i, num_facepoints, face_point_indices)
            total_face_points += num_facepoints
        elif cmd in (0x20, 0x28, 0x30):  # load matrix
            bone_index, len_and_xf_address = unpack_from('>2H', data, i)
            xf_address = 0xfff & len_and_xf_address
            length = (len_and_xf_address >> 12) + 1
            i += 4
            if cmd == 0x20:  # pos matrix
                bones.append(bone_index)
            elif cmd == 0x28:
                pass  # normals  todo figure out how these work
            else:
                raise Converter.ConvertError('Texture matrices not supported')
        else:
            raise ValueError('Unsupported draw cmd {}'.format(cmd))
    face_point_indices = np.array(face_point_indices, np.int)
    face_point_indices[:, [0, 1]] = face_point_indices[:, [1, 0]]
    # create the point collections
    g_verts = PointCollection(decode_geometry_group(vertices), face_point_indices[:, :, vertex_index],
                              vertices.minimum, vertices.maximum)
    if normals:
        g_normals = PointCollection(decode_geometry_group(normals), face_point_indices[:, :, normal_index])
    else:
        g_normals = None
    if colors:
        g_colors = ColorCollection(ColorCollection.decode_data(colors), face_point_indices[:, :, color_index])
    else:
        g_colors = None
    geo_texcoords = []
    for tex in texcoords:
        x = decode_geometry_group(tex)
        pc = PointCollection(x, face_point_indices[:, :, texcoord_index],
                             tex.minimum, tex.maximum)
        pc.flip_points()
        geo_texcoords.append(pc)
        texcoord_index += 1
    mdl0_bones = polygon.parent.bones
    if pos_matrix_index >= 0:
        pos_matrix_indices = face_point_indices[:, :, 0] / 3
        bone_table = polygon.get_bone_table()
        bones = [mdl0_bones[bone_table[i]] for i in bones]  # possibly need to do something different here
    else:
        pos_matrix_indices = None
        bones = [mdl0_bones[polygon.get_bone()]]
    face_point_indices = np.copy(face_point_indices[:, :, vertex_index:])
    geometry = Geometry(polygon.name, polygon.get_material().name, face_point_indices, g_verts,
                        geo_texcoords, g_normals, g_colors, bones, pos_matrix_indices, polygon.get_linked_bone())
    return geometry


def consolidate_data(points, face_indices):
    # First pass to detect missing points
    indices_set = {x for x in face_indices.flatten()}
    point_index_map = {}  # maps points to index
    index_remapper = {}  # map original indexes to new
    new_index = 0
    new_points = []
    point_len = len(points)
    # Next consolidate and map point indices
    for original_index in range(point_len):
        if original_index not in indices_set:  # the point isn't used!
            continue
        x = points[original_index]
        y = tuple(x)
        point_index = point_index_map.get(y)
        if not point_index:  # add
            point_index_map[y] = new_index
            index_remapper[original_index] = new_index
            new_points.append(y)
            new_index += 1
        else:
            index_remapper[original_index] = point_index
    if len(new_points) >= point_len:  # No gain
        return points
    points = np.array(new_points, points.dtype)
    # Finally, update the face indices
    face_height = len(face_indices)
    face_width = len(face_indices[0])
    for i in range(face_height):
        x = face_indices[i]
        for j in range(face_width):
            x[j] = index_remapper[x[j]]
    return points


class PointCollection:

    def __init__(self, points, face_indices, minimum=None, maximum=None):
        """
        :param points: 2-d numpy array of points
        :param face_indices: ndarray of triangle indices, indexing points
        :param minimum: the minimum value
        :param maximum: the maximum value
        """
        self.points = points
        self.face_indices = face_indices
        if not minimum or not maximum:
            self.minimum, self.maximum = self.__calc_min_max(points)
        else:
            self.minimum = [x for x in minimum]
            self.maximum = [x for x in maximum]

    def __iter__(self):
        return iter(self.points)

    def __next__(self):
        return next(self.points)

    def __len__(self):
        return len(self.points)

    @staticmethod
    def __calc_min_max(points):
        width = len(points[0])
        return [min(points[:, i]) for i in range(width)], [max(points[:, i]) for i in range(width)]

    def combine(self, point_collection):
        point_collection.face_indices += len(self)
        self.points = np.append(self.points, point_collection.points, 0)
        self.face_indices = np.append(self.face_indices, point_collection.face_indices, 0)
        for i in range(len(self.minimum)):
            if self.minimum[i] > point_collection.minimum[i]:
                self.minimum[i] = point_collection.minimum[i]
            if self.maximum[i] < point_collection.maximum[i]:
                self.maximum[i] = point_collection.maximum[i]

    def get_stride(self):
        return len(self.points[0])

    def apply_affine_matrix(self, matrix):
        """
        transforms points using the matrix (last row is ignored)
        matrix: 4x4 ndarray matrix
        """
        self.points = apply_matrix(matrix, self.points)
        self.minimum, self.maximum = self.__calc_min_max(self.points)

    @staticmethod
    def get_format_divisor(minimum, maximum):
        point_max = max(maximum)
        point_min = min(minimum)
        is_signed = True if point_min < 0 else False
        point_max = max(point_max, abs(point_min))
        max_shift = 16 - math.frexp(point_max)[1] - is_signed
        if max_shift <= 6:  # guarantee 6 decimals of precision
            return 4, 0  # float
        elif max_shift < 15:
            return 0x2 + is_signed, max_shift  # short
        return is_signed, max_shift - 8

    def flip_points(self):
        self.points[:, -1] = self.points[:, -1] * -1 + 1
        self.minimum[-1] = min(self.points[:, -1])
        self.maximum[-1] = max(self.points[:, -1])

    def encode_data(self, geometry):
        """Encodes the point collection as geometry data, returns the data width (component count)
        :type geometry: Geometry
        :type self: PointCollection
        """
        geometry.minimum = self.minimum
        geometry.maximum = self.maximum
        form, divisor = self.get_format_divisor(self.minimum, self.maximum)
        points = self.points
        point_width = len(points[0])
        if form == 4:
            geometry.stride = point_width * 4
        elif form > 1:
            geometry.stride = point_width * 2
        else:
            geometry.stride = point_width
        geometry.comp_count = geometry.COMP_COUNT.index(point_width)
        geometry.format = form
        geometry.divisor = divisor
        multiplyBy = 2 ** divisor
        data = geometry.data
        if divisor:
            if form == 3:
                dtype = np.int16
            elif form == 2:
                dtype = np.uint16
            elif form == 1:
                dtype = np.int8
            elif form == 0:
                dtype = np.uint8
            else:
                raise ValueError(f'Unexpected format {form} for divisor {divisor}')
            self.encode_points(multiplyBy, dtype)
        points = self.consolidate_points()
        geometry.count = len(self)
        if geometry.count > 0xffff:
            raise Converter.ConvertError(f'{geometry.name} has too many points! ({geometry.count})')
        for x in points:
            data.append(x)
        return form, divisor

    def consolidate_points(self, precision=None):
        points = self.points if not precision else np.around(self.points, precision)
        self.points = consolidate_data(points, self.face_indices)
        return self.points

    def encode_points(self, multiplier, dtype):
        x = np.around(self.points * multiplier)
        self.points = x.astype(dtype)


class ColorCollection:

    def __init__(self, rgba_colors, face_indices, encode_format=None, normalize=False):
        """
        :param rgba_colors: [[r,g,b,a], ...] between 0-1, normalizes to 0-255
        :param face_indices: ndarray, list of indexes for each triangle [[tri_index0, tri_index1, tri_index2], ...]
        :param encode_format: (0=rgb565|1=rgb8|2=rgb32|3=rgba4|4=rgba6|5=rgba8)
        """
        self.rgba_colors = rgba_colors
        if normalize:
            self.normalize()
        self.face_indices = face_indices
        self.encode_format = encode_format

    def __len__(self):
        return len(self.rgba_colors)

    def get_encode_format(self):
        if (self.rgba_colors[:, 3] == 255).all():
            return 1
        return 5

    def encode_data(self, color):
        rgba_colors = self.rgba_colors = self.consolidate()
        form = self.encode_format if self.encode_format is not None else self.get_encode_format()
        color.format = form
        if form < 3:
            color.stride = form + 2
            color.has_alpha = False
        else:
            color.has_alpha = True
            color.stride = form - 1
        color.count = len(rgba_colors)
        if form == 0:
            color.data = self.encode_rgb565(rgba_colors)
        elif form == 1:
            color.data = self.encode_rgb8(rgba_colors)
        elif form == 2 or form == 5:
            color.data = self.encode_rgba8(rgba_colors)
        elif form == 3:
            color.data = self.encode_rgba4(rgba_colors)
        elif form == 4:
            color.data = self.encode_rgba6(rgba_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return form

    @staticmethod
    def decode_data(color):
        form = color.format
        num_colors = len(color)
        data = color.data
        if form == 0:
            data = ColorCollection.decode_rgb565(data, num_colors)
        elif form == 1:
            data = ColorCollection.decode_rgb8(data, num_colors)
        elif form == 2 or form == 5:
            data = ColorCollection.decode_rgba8(data, num_colors)
            if form == 2:
                data[:][3] = 0xff
        elif form == 3:
            data = ColorCollection.decode_rgba4(data, num_colors)
        elif form == 4:
            data = ColorCollection.decode_rgba6(data, num_colors)
        else:
            raise ValueError('Color {} format {} out of range'.format(color.name, form))
        return np.array(data, np.uint8)

    @staticmethod
    def encode_rgb565(colors):
        data = [(x[0] & 0xf8) << 8 | (x[1] & 0xfc) << 3 | x[2] >> 3 for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def decode_rgb565(color_data, num_colors):
        data = unpack('>{}H'.format(num_colors), color_data)
        colors = []
        for color in data:
            colors.append(((color >> 8) & 0xf8, (color >> 3) & 0xfc, (color & 0x1f) << 3, 0xff))
        return colors

    @staticmethod
    def encode_rgb8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>3B', x[0], x[1], x[2]))
        return data

    @staticmethod
    def decode_rgb8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            c = list(unpack_from('>3B', data, offset))
            c.append(0xff)
            colors.append(c)
            offset += 3
        return colors

    @staticmethod
    def encode_rgba8(colors):
        data = bytearray()
        for x in colors:
            data.extend(pack('>4B', *x))
        return data

    @staticmethod
    def decode_rgba8(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            colors.append(unpack_from('>4B', data, offset))
            offset += 4
        return colors

    @staticmethod
    def encode_rgba4(colors):
        data = [(x[0] & 0xf0 | x[1] & 0xf) << 8 | x[2] & 0xf0 | x[3] & 0xf for x in colors]
        return pack('>{}H'.format(len(colors)), *data)

    @staticmethod
    def decode_rgba4(data, num_colors):
        colors = []
        c_data = unpack('>{}H'.format(num_colors), data)
        for color in c_data:
            colors.append((color >> 8 & 0xf0, color >> 4 & 0xf0,
                           color & 0xf0, color << 4 & 0xf0))
        return colors

    @staticmethod
    def encode_rgba6(colors):
        data = bytearray()
        tmp = [(x[0] & 0xfc) << 16 | (x[1] & 0xfc) << 10 | (x[2] & 0xfc) << 4 | x[3] >> 2 for x in colors]
        for x in tmp:
            data.extend(pack('>3B', x >> 16, x >> 8 & 0xff, x & 0xff))
        return data

    @staticmethod
    def decode_rgba6(data, num_colors):
        colors = []
        offset = 0
        for i in range(num_colors):
            d = unpack_from('>3B', data, offset)
            colors.append((d[0] & 0xfc, (d[0] & 0x3) << 6 | (d[1] & 0xf0) >> 2,
                           d[1] << 4 & 0xf0 | d[2] >> 4 & 0xc, d[2] << 2 & 0xfc))
            offset += 3
        return colors

    def consolidate(self):
        return consolidate_data(self.rgba_colors, self.face_indices)

    def normalize(self):
        """Normalizes data between 0-1 to 0-255"""
        self.rgba_colors = np.around(self.rgba_colors * 255).astype(np.uint8)

    def denormalize(self):
        """Opposite of normalize. returns ndarray converted from 0-255 to 0-1"""
        return self.rgba_colors.astype(np.float) / 255

    def combine(self, color):
        color.face_indices += len(self)
        self.rgba_colors = np.append(self.rgba_colors, color.rgba_colors, 0)
        self.face_indices = np.append(self.face_indices, color.face_indices, 0)


class Geometry:
    def __init__(self, name, material_name, triangles, vertices, texcoords, normals=None, colors=None,
                 bones=None, bone_indices=None, linked_bone=None):
        self.name = name
        self.vertices = vertices
        self.texcoords = texcoords
        self.normals = normals
        self.colors = colors
        self.material_name = material_name
        self.bones = bones
        self.bone_indices = bone_indices
        self.linked_bone = linked_bone
        self.triangles = triangles

    def __construct_tris(self):
        tris = [self.vertices.face_indices]
        if self.normals:
            tris.append(self.normals.face_indices)
        if self.colors:
            tris.append(self.colors.face_indices)
        for texcoord in self.texcoords:
            tris.append(texcoord.face_indices)
        return np.stack(tris, -1)

    def geometry_matches(self, geometry):
        return not (self.material_name != geometry.material_name or \
                    self.linked_bone is not geometry.linked_bone or \
                    ((self.normals is None) ^ (geometry.normals is None)) or \
                    ((self.colors is None) ^ (geometry.colors is None)) or \
                    len(self.texcoords) != len(geometry.texcoords))

    def combine(self, geometry):
        if not self.geometry_matches(geometry):
            return False
        self.vertices.combine(geometry.vertices)
        mine = self.texcoords
        theres = geometry.texcoords
        for i in range(len(mine)):
            mine[i].combine(theres[i])
        if self.normals:
            self.normals.combine(geometry.normals)
        if self.colors:
            self.colors.combine(geometry.colors)
        self.triangles = np.append(self.triangles, geometry.triangles, 0)
        return True
        # todo bone indices

    def swap_y_z_axis(self):
        collections = [self.vertices, self.normals]
        points = self.vertices.points
        points[:, [1, 2]] = points[:, [2, 1]]
        points[:, 2] *= -1
        points = self.normals.points
        points[:, [1, 2]] = points[:, [2, 1]]

    def apply_linked_bone_bindings(self):
        self.apply_matrix(np.array(self.linked_bone.get_transform_matrix(), np.float))

    def apply_matrix(self, matrix):
        self.vertices.apply_affine_matrix(matrix)

    def encode(self, mdl, bone=None):
        p = Polygon(self.name, mdl)
        fmt_str = '>'
        fmt_str += self.__encode_vertices(p, self.vertices, mdl)
        fmt_str += self.__encode_normals(p, self.normals, mdl)
        fmt_str += self.__encode_colors(p, self.colors, mdl)
        fmt_str += self.__encode_texcoords(p, self.texcoords, mdl)
        if self.__encode_tris(p, self.__construct_tris(), fmt_str):
            mdl.add_to_group(mdl.objects, p)
            if not bone:
                bone = self.linked_bone
                if not bone:
                    if not mdl.bones:
                        mdl.add_bone(mdl.name)
                    bone = mdl.bones[0]
            material = mdl.getMaterialByName(self.material_name)
            mdl.add_definition(material, p, bone)
            if self.colors:
                material.enable_vertex_color()
        return p

    def __encode_tris(self, polygon, tris, fmt_str):
        tris[:, [0, 1]] = tris[:, [1, 0]]
        triset = TriangleSet(tris)
        if not triset:
            return False
        data, polygon.face_count, polygon.facepoint_count = triset.get_tri_strips(fmt_str)
        past_align = len(data) % 32
        if past_align:
            data.extend(b'\0' * (32 - past_align))
        polygon.vt_data = data
        return True

    def __encode_vertices(self, polygon, vertices, mdl0):
        vert = Vertex(self.name, mdl0)
        mdl0.add_to_group(mdl0.vertices, vert)
        polygon.vertex_format, polygon.vertex_divisor = vertices.encode_data(vert)
        polygon.vertex_group_index = vert.index
        polygon.vertex_index_format, fmt_str = get_index_format(vert)
        return fmt_str

    def __encode_normals(self, polygon, normals, mdl0):
        if normals:
            normal = Normal(self.name, mdl0)
            polygon.normal_format = normals.encode_data(normal)[0]
            mdl0.add_to_group(mdl0.normals, normal)
            polygon.normal_type = normal.comp_count
            polygon.normal_group_index = normal.index
            polygon.normal_index_format, fmt_str = get_index_format(normal)
        else:
            polygon.normal_index_format = polygon.INDEX_FORMAT_NONE
            polygon.normal_group_index = -1
            fmt_str = ''
        return fmt_str

    def __encode_colors(self, polygon, colors, mdl0):
        if colors:
            color = Color(self.name, mdl0)
            polygon.color0_format = colors.encode_data(color)
            mdl0.add_to_group(mdl0.colors, color)
            polygon.color0_index_format, fmt_str = get_index_format(color)
            polygon.color_group_indices[0] = color.index
            polygon.num_colors = 1
        else:
            polygon.color0_index_format = polygon.INDEX_FORMAT_NONE
            polygon.num_colors = 0
            polygon.color_group_indices[0] = -1
            fmt_str = ''
        return fmt_str

    def __encode_texcoords(self, polygon, texcoords, mdl0):
        fmt_str = ''
        if texcoords:
            uv_i = len(mdl0.texCoords)
            for i in range(len(texcoords)):
                x = texcoords[i]
                tex = TexCoord(self.name + '#{}'.format(i), mdl0)
                # convert xy to st
                x.flip_points()
                polygon.tex_format[i], polygon.tex_divisor[i] = x.encode_data(tex)
                tex.index = uv_i + i
                mdl0.texCoords.append(tex)
                polygon.tex_index_format[i], fmt = get_index_format(tex)
                fmt_str += fmt
                polygon.tex_coord_group_indices[i] = tex.index
        else:
            polygon.tex_coord_group_indices[0] = -1
            polygon.tex_index_format[0] = polygon.INDEX_FORMAT_NONE
        return fmt_str

class Material:
    def __init__(self, name, diffuse_map=None, ambient_map=None, specular_map=None, transparency=0):
        self.name = name
        self.ambient_map = ambient_map
        self.diffuse_map = diffuse_map
        self.specular_map = specular_map
        self.transparency = transparency

    def get_maps(self):
        maps = set()
        maps.add(self.ambient_map)
        maps.add(self.diffuse_map)
        maps.add(self.specular_map)
        if None in maps:
            maps.remove(None)
        return maps

    @staticmethod
    def encode_map(map, material, used_layers):
        if map:
            layer_name = os.path.splitext(os.path.basename(map))[0]
            if layer_name not in used_layers:
                material.addLayer(layer_name)
                used_layers.add(layer_name)

    def encode(self, mdl):
        m = material.Material.get_unique_material(self.name, mdl)
        mdl.add_material(m)
        if self.transparency > 0:
            m.enable_blend()
        # maps
        layers = set()
        self.encode_map(self.diffuse_map, m, layers)
        self.encode_map(self.ambient_map, m, layers)
        self.encode_map(self.specular_map, m, layers)
        return m


class Controller:
    def __init__(self, name, bind_shape_matrix, inv_bind_matrix, bones, weights, vertex_weight_counts,
                 vertex_weight_indices,
                 geometry):
        self.name = name
        self.bind_shape_matrix = bind_shape_matrix
        self.inv_bind_matrix = inv_bind_matrix
        self.bones = bones
        self.weights = weights
        self.vertex_weight_counts = vertex_weight_counts
        self.vertex_weight_indices = vertex_weight_indices
        self.geometry = geometry

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, matrix=None):
        matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        return self.geometry


def float_to_str(fl):
    return format(fl, '.8f') if 0.0001 > fl > -0.0001 else str(fl)
