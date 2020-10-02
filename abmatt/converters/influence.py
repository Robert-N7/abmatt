import numpy as np

from converters.matrix import apply_matrix, apply_matrix_single


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
        self.weights = [] if weights is None else weights
        self.matrix = None

    def get_matrix(self):
        if self.matrix is None:
            # calculate matrix
            matrix = None
            for weight in self.weights:
                if matrix is None:
                    matrix = weight.bone.get_transform_matrix()
                else:
                    matrix = np.dot(matrix, weight.bone.get_transform_matrix())
            self.matrix = matrix
        return self.matrix

    def apply(self, vertex):
        """Takes a vertex and apply influence"""
        if self.is_mixed():
            return vertex
        matrix = self.get_matrix()
        return apply_matrix_single(matrix, vertex)

    def apply_all(self, vertices):
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
        l = len(self)
        if l != len(other):
            return False
        for i in range(l):
            if self[i] != other[i]:
                return False
        return True

    def append(self, weight):
        self.weights.append(weight)


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
            influences[weight_id] = Influence([Weight(bones[bonetable[weight_id]], 1)])
        for inf in nodemix.mixed_weights:
            weight_id = inf.weight_id
            influences[weight_id] = Influence([Weight(bones[bonetable[x[0]]], x[1]) for x in inf])
    else:
        for i in range(len(bonetable)):
            index = bonetable[i]
            influences[i] = Influence(weights=[Weight(bones[bonetable[index]], 1)])
    return InfluenceCollection(influences)