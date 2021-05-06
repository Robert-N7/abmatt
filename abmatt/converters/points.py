import math

import numpy as np

from abmatt.converters import error
from abmatt.converters.matrix import combine_matrices, apply_matrix


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
        self.matrix = None
        self.influences = None
        assert np.max(face_indices) < len(points)
        self.minimum = minimum
        self.maximum = maximum

    def __eq__(self, other):
        return other is not None and type(other) == PointCollection and np.allclose(self.points, other.points) and \
               self.face_indices == other.face_indices

    def __iter__(self):
        return iter(self.points)

    def __next__(self):
        return next(self.points)

    def __len__(self):
        return len(self.points)

    def __getitem__(self, item):
        return self.points[item]

    def __setitem__(self, key, value):
        self.points[key] = value

    @staticmethod
    def __calc_min_max(points):
        width = len(points[0])
        return [min(points[:, i]) for i in range(width)], [max(points[:, i]) for i in range(width)]

    def combine(self, point_collection):
        point_collection.face_indices += len(self)
        self.points = np.append(self.points, point_collection.points, 0)
        self.face_indices = np.append(self.face_indices, point_collection.face_indices, 0)
        if not self.minimum:
            self.minimum, self.maximum = self.__calc_min_max(self.points)
        if not point_collection.minimum:
            point_collection.minimum, point_collection.maximum = point_collection.__calc_min_max(self.points)
        for i in range(len(self.minimum)):
            if self.minimum[i] > point_collection.minimum[i]:
                self.minimum[i] = point_collection.minimum[i]
            if self.maximum[i] < point_collection.maximum[i]:
                self.maximum[i] = point_collection.maximum[i]

    def get_stride(self):
        return len(self.points[0])

    def apply_affine_matrix(self, matrix, apply=True):
        """
        transforms points using the matrix (last row is ignored)
        matrix: 4x4 ndarray matrix
        apply: apply immediately if true, otherwise store in matrix
        """
        self.matrix = combine_matrices(matrix, self.matrix)
        if apply:
            self.points = apply_matrix(self.matrix, self.points)
            self.matrix = None

    def apply_rotation_matrix(self, rotation_matrix):
        if rotation_matrix is not None and not np.allclose(rotation_matrix, np.identity(3)):
            # if self.matrix is not None:
            #     self.points = apply_matrix(self.matrix, self.points)
            #     self.matrix = None
            for i in range(len(self.points)):
                self.points[i] = np.dot(rotation_matrix, self.points[i])

    @staticmethod
    def get_format_divisor(minimum, maximum):
        point_max = max(maximum)
        point_min = min(minimum)
        is_signed = True if point_min < 0 else False
        point_max = max(point_max, abs(point_min))
        max_shift = 16 - math.frexp(point_max)[1] - is_signed
        if max_shift <= 6:  # guarantee 6 decimals of precision
            return 'f', 0  # float
        elif max_shift >= 15:
            max_shift -= 8
            format = 'b' if is_signed else 'B'
        else:
            format = 'h' if is_signed else 'H'
        return format, max_shift

    def flip_points(self):
        self.points[:, -1] = self.points[:, -1] * -1 + 1

    def encode_data(self, mdl0_points, get_index_remapper=False, encoder=None, influences=None):
        """Encodes the point collection as geometry data, returns the data width (component count)
        :param get_index_remapper: set to true to get the index remapping, (useful for influences)
        :type mdl0_points: Points
        :type self: PointCollection
        """
        if self.matrix is not None:
            self.points = apply_matrix(self.matrix, self.points)
            self.matrix = None
        if influences is not None:
            self.influences = influences
        self.minimum, self.maximum = self.__calc_min_max(self.points)
        mdl0_points.minimum = self.minimum
        mdl0_points.maximum = self.maximum
        if encoder is not None:
            encoder.before_encode(self)
            form = encoder.get_format()
            divisor = encoder.get_divisor()
        else:
            form, divisor = self.get_format_divisor(self.minimum, self.maximum)
        points = self.points
        point_width = len(points[0])
        mdl0_points.comp_count = mdl0_points.comp_count_from_width(point_width)
        mdl0_points.divisor = divisor
        data = mdl0_points.data
        if form == 'h':
            mdl0_points.format = 3
            dtype = np.int16
            mdl0_points.stride = point_width * 2
        elif form == 'H':
            mdl0_points.format = 2
            dtype = np.uint16
            mdl0_points.stride = point_width * 2
        elif form == 'b':
            mdl0_points.format = 1
            dtype = np.int8
            mdl0_points.stride = point_width
        elif form == 'B':
            mdl0_points.format = 0
            dtype = np.uint8
            mdl0_points.stride = point_width
        elif form == 'f':
            mdl0_points.format = 4
            dtype = np.float
            mdl0_points.stride = point_width * 4
        else:
            raise error.ConvertError('Unknown format {}'.format(form))
        if divisor:
            multiplyBy = 2 ** divisor
            self.encode_points(multiplyBy, dtype)
        should_consolidate = False if self.influences and self.influences.is_mixed() else encoder is None or encoder.should_consolidate()
        if should_consolidate:
            points, face_indices, index_remapper = self.__consolidate_points()
            self.points = points
            self.face_indices = face_indices
        else:
            index_remapper = None
            points = self.points
        mdl0_points.count = len(points)
        if mdl0_points.count > 0xffff:
            raise error.ConvertError(f'{mdl0_points.name} has too many points! ({mdl0_points.count})')
        for x in points:
            data.append(x)
        self.points = points
        if encoder:
            encoder.after_encode(mdl0_points)
        if get_index_remapper:
            return form, divisor, index_remapper
        return form, divisor

    def __consolidate_points(self, precision=None):
        points = self.points if not precision else np.around(self.points, precision)
        return consolidate_data(points, self.face_indices)

    def encode_points(self, multiplier, dtype):
        x = np.around(self.points * multiplier)
        self.points = x.astype(dtype)


def remap_face_points(face_indices, index_remapper):
    cpy = np.copy(face_indices)
    for k, v in index_remapper.items():
        cpy[face_indices == k] = v
    return cpy


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
        return points, face_indices, None
    points = np.array(new_points, points.dtype)
    # Finally, update the face indices
    face_indices = remap_face_points(face_indices, index_remapper)
    return points, face_indices, index_remapper