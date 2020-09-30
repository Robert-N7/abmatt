import numpy as np


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

    def get_influences(self):
        vert_influences = []
        index = 0
        indices = self.vertex_weight_indices
        weights = self.weights
        bones = self.bones
        for vert_weight_count in self.vertex_weight_counts:
            influence = []
            for i in range(vert_weight_count):
                influence.append(Influence(bones[indices[index]], weights[indices[index + 1]]))
                index += 2
            vert_influences.append(influence)
        return vert_influences

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, matrix=None):
        # matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        return self.geometry


class Influence:
    def __init__(self, bone, weight):
        self.bone = bone
        self.weight = weight