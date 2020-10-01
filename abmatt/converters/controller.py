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

    @staticmethod
    def __add_bone(bone, bone_map):
        i = len(bone_map)
        bone_map[bone] = i
        return i

    def get_influences(self, bone_map):
        """
        :param bone_map: map of bone names to indices
        :returns influence collection
        """
        # construct my own bone map to map indices
        my_bone_map = []
        bones = self.bones
        for i in range(len(bones)):
            index = bone_map.get(bones[i])
            if index is not None:
                my_bone_map.append(index)
            else:
                my_bone_map.append(self.__add_bone(bones[i], bone_map))
        facepoint_indices = []   # maps the face point index to influence index
        influences = []
        index = 0
        indices = self.vertex_weight_indices
        weights = self.weights
        vertex_weight_counts = self.vertex_weight_counts
        # Now construct influences
        for facepoint_index in range(len(vertex_weight_counts)):
            vert_weight_count = vertex_weight_counts[facepoint_index]
            influence = []
            for i in range(vert_weight_count):
                inf = indices[index]
                influence.append((inf[0], weights[inf[1]]))
                index += 1
            found = False
            for i in range(len(influences)):
                if influence == influences[i]:
                    found = True
                    facepoint_indices.append(i)
                    break
            if not found:
                facepoint_indices.append(len(influences))
                influences.append(np.array(influence, float))
        return InfluenceCollection(influences, np.array(facepoint_indices, dtype=np.uint), my_bone_map)

    def has_multiple_weights(self):
        return not np.min(self.vertex_weight_counts) == np.max(self.vertex_weight_counts) == 1.0

    def get_bound_geometry(self, bone_map, matrix=None):
        # matrix = combine_matrices(matrix, self.bind_shape_matrix)
        self.geometry.apply_matrix(matrix)
        self.geometry.influences = self.get_influences(bone_map)
        return self.geometry


class InfluenceCollection:
    def __init__(self, influences, face_indices, bone_indices=None):
        """
        :param influences:  list of lists of tuples [[(bone_id, weight), ..], ...]
        :param face_indices: np array of face_indices that map to influences
        """
        self.influences = influences
        self.face_indices = face_indices
        if bone_indices is None:
            bone_indices = set()
            for x in influences:
                for y in x:
                    bone_indices.add(y[0])
        self.bone_indices = bone_indices

    def __len__(self):
        return len(self.influences)

    def __iter__(self):
        return iter(self.influences)

    def __next__(self):
        return next(self.influences)



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