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

    def get_influences(self, bone_map):
        """
        :param bone_map: map of bone names to bones
        :returns influence collection
        """
        # construct my own bone map
        my_bone_map = [bone_map[name] for name in self.bones]
        influences = []
        indices = self.vertex_weight_indices
        weights = self.weights
        vertex_weight_counts = self.vertex_weight_counts
        vertex_influence_map = {}
        # Now construct influences
        for vertex_index in range(len(vertex_weight_counts)):
            weight_count = vertex_weight_counts[vertex_index]
            influence = Influence([Weight(my_bone_map[indices[i, 0]], weights[indices[i, 1]]) for i in range(weight_count)])
            # consolidate along the way by checking for duplicate influences
            found = False
            for i in range(len(influences)):
                if influence == influences[i]:
                    found = True
                    vertex_influence_map[vertex_index] = influences[i]
                    break
            if not found:
                vertex_influence_map[vertex_index] = influence
                influences.append(influence)
        return InfluenceCollection(influences, vertex_influence_map)

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, bone_map, matrix=None):
        # matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        self.geometry.influences = self.get_influences(bone_map)
        return self.geometry



# class Weight:
#     """A weight has a number of influences"""
#     def __init__(self, influences):
#         self.influences = influences
#
#     def __len__(self):
#         return len(self.influences)
#
#     def __getitem__(self, item):
#         return self.influences[item]
#
#     def __setitem__(self, key, value):
#         self.influences[key] = value
#
#     def __eq__(self, other):
#         if len(self) != len(other):
#             return False
#         for i in range(len(self)):
#             if self[i] != other[i]:
#                 return False
#         return True
#
#     def __iter__(self):
#         return iter(self.influences)
#
#     def __next__(self):
#         return next(self.influences)


# class Influence:
#     def __init__(self, bone, weight):
#         self.bone = bone
#         self.weight = weight
#
#     def __eq__(self, other):
#         return self.bone == other.bone and self.weight == other.weight



