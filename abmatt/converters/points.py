import math

import numpy as np

from converters.convert_lib import Converter
from converters.matrix import apply_matrix


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

    def encode_data(self, points, remap_indices=None):
        """Encodes the point collection as geometry data, returns the data width (component count)
        :type points: Points
        :type self: PointCollection
        :type remap_indices: list of np arrays to have their facepoint indices remapped
        """
        points.minimum = self.minimum
        points.maximum = self.maximum
        form, divisor = self.get_format_divisor(self.minimum, self.maximum)
        points = self.points
        point_width = len(points[0])
        if form == 4:
            points.stride = point_width * 4
        elif form > 1:
            points.stride = point_width * 2
        else:
            points.stride = point_width
        points.comp_count = points.COMP_COUNT.index(point_width)
        points.format = form
        points.divisor = divisor
        multiplyBy = 2 ** divisor
        data = points.data
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
        points, index_remapper = self.__consolidate_points()
        if index_remapper and remap_indices:
            for indices in remap_indices:
                self.remap_face_points(indices, index_remapper)
        points.count = len(self)
        if points.count > 0xffff:
            raise Converter.ConvertError(f'{points.name} has too many points! ({points.count})')
        for x in points:
            data.append(x)
        self.points = points
        return form, divisor

    @staticmethod
    def remap_face_points(face_indices, index_remapper):
        face_height = len(face_indices)
        face_width = len(face_indices[0])
        for i in range(face_height):
            x = face_indices[i]
            for j in range(face_width):
                x[j] = index_remapper[x[j]]

    def __consolidate_points(self, precision=None):
        points = self.points if not precision else np.around(self.points, precision)
        return consolidate_data(points, self.face_indices)

    def encode_points(self, multiplier, dtype):
        x = np.around(self.points * multiplier)
        self.points = x.astype(dtype)


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
        return points, None
    points = np.array(new_points, points.dtype)
    # Finally, update the face indices
    PointCollection.remap_face_points(face_indices, index_remapper)
    return points, index_remapper