import numpy as np

from converters.influence import Influence, Weight, InfluenceCollection


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
        influences = {}
        indices = self.vertex_weight_indices
        weights = self.weights
        vertex_weight_counts = self.vertex_weight_counts
        # Now construct influences
        for vertex_index in range(len(vertex_weight_counts)):
            weight_count = vertex_weight_counts[vertex_index]
            influence = Influence()
            for i in range(weight_count):
                bone = my_bone_map[indices[i, 0]]
                influence[bone.name] = Weight(bone, weights[indices[i, 1]])
            # consolidate along the way by checking for duplicate influences
            found = False
            for i in range(len(influences)):
                if influence == influences[i]:
                    found = True
                    influences[vertex_index] = influences[i]
                    break
            if not found:
                influences[vertex_index] = influence
        return InfluenceCollection(influences)

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, bone_map, matrix=None):
        # matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        self.geometry.influences = self.get_influences(bone_map)
        return self.geometry


def get_controller(geometry):
    influences = geometry.influences
    bones = []
    vert_counts = []
    indexer = []
    weights = []
    bone_index = weight_index = 0
    use_single = True if len(influences) == len(geometry.vertices) else False
    for vert_index in range(len(geometry.vertices)):
        inf = influences[vert_index] if use_single else influences[0]
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
    bind_matrix = np.array(geometry.linked_bone.get_transform_matrix(), np.float)
    bind_matrix[:3, 3] = 0  # 0 out translation
    return Controller(geometry.name, bind_matrix, inv_bind_matrix, bone_names, np.array(weights, float),
                      vert_counts, np.array(indexer, np.uint), geometry)
