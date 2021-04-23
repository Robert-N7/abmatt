import math

import numpy as np

IDENTITY = np.identity(4)


def apply_matrix_single(matrix, point):
    return np.dot(matrix[:3], np.append(point, 1))


def rotation_matrix_to_transform(matrix):
    return np.append(np.append(matrix, np.array([0] * 3).reshape((3, 1)), 1), np.array([[0, 0, 0, 1]]), 0)


def apply_matrix(matrix, points):
    if np.allclose(matrix, IDENTITY):
        return points
    matrix = matrix[:3]
    # add a 1 after each point (for transformation)
    new_col = np.full((len(points), 1), 1, dtype=float)
    return np.array([matrix.dot(x) for x in np.append(points, new_col, 1)])


def srt_to_matrix(scale=(1, 1, 1), rotation=(0, 0, 0), translation=(0, 0, 0)):
    matrix = euler_to_rotation_matrix(rotation)
    for i in range(3):
        matrix[:, i] = matrix[:, i] * scale[i]
    matrix = np.append(matrix, np.array(translation, float).reshape((3, 1)), 1)
    return np.append(matrix, np.array([[0, 0, 0, 1]], float), 0)


def matrix_to_srt(matrix):
    """Takes a matrix and returns scale, rotation, translation"""
    translation = matrix[:, 3][:3]
    matrix, scale = get_rotation_matrix(matrix, True)
    rotation = rotation_matrix_to_euler(matrix)
    return scale, rotation, translation


def get_rotation_matrix(matrix, get_scale=False):
    scale = [round(vector_magnitude(matrix[:, 0]), 4),
             round(vector_magnitude(matrix[:, 1]), 4),
             round(vector_magnitude(matrix[:, 2]), 4)]
    rotation_matrix = np.swapaxes([[matrix[j, i] / scale[i] for j in range(3)] for i in range(3)],
                                  0, 1)
    if get_scale:
        return rotation_matrix, scale
    return rotation_matrix


def euler_to_rotation_matrix(euler_angles):
    x, y, z = np.array(euler_angles, float) * math.pi / 180
    rot_x = np.array([[1, 0, 0],
                      [0, math.cos(x), -math.sin(x)],
                      [0, math.sin(x), math.cos(x)]], dtype=float)

    rot_y = np.array([[math.cos(y), 0, math.sin(y)],
                      [0, 1, 0],
                      [-math.sin(y), 0, math.cos(y)]], dtype=float)

    rot_z = np.array([[math.cos(z), -math.sin(z), 0],
                      [math.sin(z), math.cos(z), 0],
                      [0, 0, 1]], dtype=float)
    y_x = np.matmul(rot_y, rot_x)
    matrix = np.matmul(rot_z, y_x)
    return matrix


def rotation_matrix_to_euler(matrix):
    # Calculates rotation matrix to euler angles
    # assert (isRotationMatrix(matrix))
    sy = math.sqrt(matrix[0, 0] * matrix[0, 0] + matrix[1, 0] * matrix[1, 0])
    singular = sy < 1e-6
    if not singular:
        x = math.atan2(matrix[2, 1], matrix[2, 2])
        y = math.atan2(-matrix[2, 0], sy)
        z = math.atan2(matrix[1, 0], matrix[0, 0])
    else:
        x = math.atan2(-matrix[1, 2], matrix[1, 1])
        y = math.atan2(-matrix[2, 0], sy)
        z = 0
    return np.round(np.array([x, y, z]) * 180 / math.pi, 3)


def scale_matrix(matrix, scale):
    for i in range(len(scale)):
        matrix[:, i] = matrix[:, i] * scale[i]
    return matrix


def rotate_matrix(matrix, rotation):
    x = np.append(euler_to_rotation_matrix(rotation), np.array([[0] * 3]).reshape((3, 1)), axis=1)
    return np.matmul(matrix, np.append(x, np.array([[0, 0, 0, 1]]), 0))


def translate_matrix(matrix, translation):
    for i in range(3):
        matrix[i, 3] += translation[i]
    return matrix


def combine_matrices(matrix1, matrix2):
    if matrix1 is None:
        return matrix2
    elif matrix2 is None:
        return matrix1
    else:
        return np.matmul(matrix1, matrix2)


# # Checks if a matrix is a valid rotation matrix.
# def isRotationMatrix(R):
#     Rt = np.transpose(R)
#     shouldBeIdentity = np.dot(Rt, R)
#     I = np.identity(R.shape[0], dtype=R.dtype)
#     n = np.linalg.norm(I - shouldBeIdentity)
#     return n < 1e-6

def vector_magnitude(vector):
    return math.sqrt(sum(x ** 2 for x in vector))


def get_transform_matrix(scale, rotation, translation):
    """Gets the transform matrix based on scale, rotation, translation"""
    deg2rad = math.pi / 180
    cosx = math.cos(rotation[0] * deg2rad)
    sinx = math.sin(rotation[0] * deg2rad)
    cosy = math.cos(rotation[1] * deg2rad)
    siny = math.sin(rotation[1] * deg2rad)
    cosz = math.cos(rotation[2] * deg2rad)
    sinz = math.sin(rotation[2] * deg2rad)

    return np.array([[scale[0] * cosy * cosz, scale[0] * sinz * cosy, -scale[0] * siny, 0.0],
                     [scale[1] * (sinx * cosz * siny - cosx * sinz), scale[1] * (sinx * sinz * siny + cosz * cosx),
                      scale[1] * sinx * cosy, 0.0],
                     [scale[2] * (sinx * sinz + cosx * cosz * siny), scale[2] * (cosx * sinz * siny - sinx * cosz),
                      scale[2] * cosx * cosy, 0.0],
                     [translation[0], translation[1], translation[2], 1.0]], float)


def get_inv_transform_matrix(scale, rotation, translation):
    deg2rad = math.pi / 180
    cosx = math.cos(rotation[0] * deg2rad)
    sinx = math.sin(rotation[0] * deg2rad)
    cosy = math.cos(rotation[1] * deg2rad)
    siny = math.sin(rotation[1] * deg2rad)
    cosz = math.cos(rotation[2] * deg2rad)
    sinz = math.sin(rotation[2] * deg2rad)
    scale = (1. / scale[0], 1. / scale[1], 1. / scale[2])
    translation = np.array(translation) * -1
    rs = np.array([[scale[0] * cosy * cosz, scale[1] * (sinx * siny * cosz - cosx * sinz),
                    scale[2] * (cosx * siny * cosz + sinx * sinz), 0.0],
                   [scale[0] * cosy * sinz, scale[1] * (sinx * siny * sinz + cosx * cosz),
                    scale[2] * (cosx * siny * sinz - sinx * cosz), 0.0],
                   [-scale[0] * siny, scale[1] * sinx * cosy, scale[2] * cosx * cosy, 0.0]], float)
    return np.append(rs,
                     [[(translation[0] * rs[0, 0]) + (translation[1] * rs[1, 0]) + (translation[2] * rs[2, 0]),
                      (translation[0] * rs[0, 1]) + (translation[1] * rs[1, 1]) + (translation[2] * rs[2, 1]),
                      (translation[0] * rs[0, 2]) + (translation[1] * rs[1, 2]) + (translation[2] * rs[2, 2]), 1.0]],
                     axis=0
                     )
