import numpy as np

from abmatt.converters.influence import Influence, Weight, InfluenceCollection, Joint
from abmatt.converters.matrix import combine_matrices


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

    def __order_bones(self, bone_map):
        bones = self.bones
        controller_matrices = self.inv_bind_matrix.reshape((-1, 4, 4))
        bone_matrices = [Joint.get_world_position(bone_map[bone]) for bone in bones]
        new_bone_map = []
        for i in range(len(controller_matrices)):
            test_matrix = controller_matrices[i]
            # if not np.allclose(bone_matrices[i], test_matrix, 0.0001):
            #     raise ValueError(f'Controller {self.name} matrix does not match bone matrix\n{test_matrix}')
            new_bone_map.append(bone_map[bones[i]])
        return new_bone_map, controller_matrices

    def get_influences(self, bone_map, all_influences):
        """
        :param bone_map: map of bone names to bones
        :returns influence collection
        """
        # construct my own bone map
        # my_bone_map = [bone_map[name] for name in self.bones]
        weights = self.weights
        my_bone_map, matrices = self.__order_bones(bone_map)
        if len(self.bones) == 1 and np.allclose(weights, 1.0):     # No influence needed
            influence = Influence()
            influence[my_bone_map[0].name] = Weight(my_bone_map[0], 1.0)
            influence = all_influences.create_or_find(influence)
            self.geometry.apply_matrix(matrices[0])
            return InfluenceCollection({0: influence})
        influences = {}
        indices = self.vertex_weight_indices
        vertex_weight_counts = self.vertex_weight_counts
        j = 0
        # Now construct influences
        vertices = self.geometry.vertices
        for vertex_index in range(len(vertex_weight_counts)):
            weight_count = vertex_weight_counts[vertex_index]
            influence = Influence()
            for i in range(weight_count):
                bone = my_bone_map[indices[j, 0]]
                influence[bone.name] = Weight(bone, weights[indices[j, 1]])
                j += 1
            influences[vertex_index] = all_influences.create_or_find(influence)
            # apply_matrix(matrices[] vertices[vertex_index]
        return InfluenceCollection(influences)

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, bone_map, all_influences, matrix=None):
        matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        self.geometry.influences = influences = self.get_influences(bone_map, all_influences)
        return self.geometry, influences


def get_controller(geometry):
    influences = geometry.influences
    bone_index = weight_index = 0
    # if there's not an even number of influences per vertices, use a default (weight 1)
    if len(influences) != len(geometry.vertices):
        inf = influences[0]
        vert_counts = [1] * len(geometry.vertices)
        bones = [inf[x].bone for x in inf]
        weights = [1]
        indexer = [0] * (2 * len(geometry.vertices))
    else:   # build the weights per vertex
        bones = []
        vert_counts = []
        indexer = []
        weights = []
        for vert_index in range(len(geometry.vertices)):
            inf = influences[vert_index]
            vert_counts.append(len(inf))
            for bone_name in inf:
                x = inf[bone_name]
                bone = x.bone
                try:
                    bone_id = bones.index(bone)
                except ValueError:
                    bones.append(bone)
                    bone_id = bone_index
                    bone_index += 1
                indexer.append((bone_id, weight_index))
                weights.append(x.weight)
                weight_index += 1
    vert_counts = np.array(vert_counts, dtype=np.uint)
    bone_names = [x.name for x in bones]
    inv_bind_matrix = np.array([x.get_inv_transform_matrix() for x in bones], np.float)
    # bind_matrix = np.array(geometry.linked_bone.get_transform_matrix(), np.float)
    # bind_matrix[:3, 3] = 0  # 0 out translation
    bind_matrix = np.identity(4)
    return Controller(geometry.name, bind_matrix, inv_bind_matrix, bone_names, np.array(weights, float),
                      vert_counts, np.array(indexer, np.uint), geometry)
