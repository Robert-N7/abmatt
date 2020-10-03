import numpy as np

from converters.matrix import apply_matrix, apply_matrix_single, get_rotation_matrix, scale_matrix, translate_matrix


class Joint:
    def __init__(self, name, matrix=None):
        self.name = name
        self.matrix = matrix if matrix is not None else np.identity(4)
        self.children = None

    def get_transform_matrix(self):
        return self.matrix

    def get_inv_transform_matrix(self):
        return np.linalg.inv(self.matrix)


class Influence:
    def __init__(self, weights=None):
        self.weights = {} if weights is None else weights
        self.rotation_matrix = self.matrix = None

    def get_matrix(self):
        if self.matrix is None:
            # calculate matrix
            matrix = None
            for bone in self.weights:
                weight = self.weights[bone]
                if matrix is None:
                    matrix = np.array(weight.bone.get_transform_matrix())
                    # self.rotation_matrix, scale = get_rotation_matrix(matrix, True)
                    # mtx = scale_matrix(np.identity(4), scale)
                    # matrix = translate_matrix(mtx, matrix[:, 3])
                else:
                    matrix = np.dot(matrix, weight.bone.get_transform_matrix())
            self.matrix = matrix
        return self.matrix

    def apply_to(self, vertex):
        """Takes a vertex and apply influence"""
        if self.is_mixed():
            return vertex
        matrix = self.get_matrix()
        return apply_matrix_single(matrix, vertex)

    def apply_to_all(self, vertices):
        if self.is_mixed():
            return vertices
        matrix = self.get_matrix()
        return apply_matrix(matrix, vertices)

    def is_mixed(self):
        return len(self.weights) > 1

    def __len__(self):
        return len(self.weights)

    def __iter__(self):
        return iter(self.weights)

    def __next__(self):
        return next(self.weights)

    def __getattr__(self, item):
        return self.weights[item]

    def __eq__(self, other):
        return self.weights == other.weights

    def __setitem__(self, key, value):
        self.weights[key] = value

    def __getitem__(self, item):
        return self.weights[item]


class Weight:
    def __init__(self, bone, weight):
        self.bone = bone
        self.weight = weight

    def __eq__(self, other):
        return self.bone == other.bone and self.weight == other.weight


class InfluenceCollection:
    def __init__(self, influences, vertex_id_map=None):
        """
        :param influences:  list of influences
        :param vertex_id_map: maps vertices to influences
        """
        self.influences = influences
        self.vertex_id_map = vertex_id_map

    def __len__(self):
        return len(self.influences)

    def __iter__(self):
        return iter(self.influences)

    def __next__(self):
        return next(self.influences)

    def __getitem__(self, item):
        return self.influences[item]

    def __eq__(self, other):
        return self.influences == other.influences


def decode_mdl0_influences(mdl0):
    bones = mdl0.bones
    bonetable = mdl0.boneTable
    influences = {}
    nodemix = mdl0.NodeMix
    if nodemix is not None:
        for weight in nodemix.fixed_weights:
            weight_id = weight.weight_id
            bone = bones[bonetable[weight_id]]
            influences[weight_id] = Influence({bone.name: Weight(bone, 1)})
        for inf in nodemix.mixed_weights:
            weight_id = inf.weight_id
            influences[weight_id] = influence = Influence()
            for x in inf:
                bone = bones[bonetable[x[0]]]
                influence[bone.name] = Weight(bone, x[1])
    else:
        for i in range(len(bonetable)):
            index = bonetable[i]
            bone = bones[bonetable[index]]
            influences[i] = Influence(weights={bone.name: Weight(bone, 1)})
    return InfluenceCollection(influences)
