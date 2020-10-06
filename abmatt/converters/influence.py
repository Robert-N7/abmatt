import numpy as np

from brres.mdl0.definition import get_definition
from converters.matrix import apply_matrix, apply_matrix_single, get_rotation_matrix, scale_matrix, translate_matrix, \
    rotation_matrix_to_transform


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
    """
    Influence is used for skins to determine how bones effect vertices
    An influence consists of a number of bone weights, the bone matrices
    are combined using their corresponding weights to get a transformation matrix,
    which is applied to the vertices.
    """

    def __init__(self, bone_weights=None, influence_id=None):
        self.bone_weights = {} if bone_weights is None else bone_weights
        self.rotation_matrix = self.matrix = self.inv_matrix = None
        self.influence_id = influence_id

    def calc_matrix(self, bone, matrix=None, inverse=False):
        if bone is None:
            return matrix
        bone_matrix = bone.get_transform_matrix() if not inverse else bone.get_inv_transform_matrix()
        matrix = np.dot(bone_matrix, matrix) if matrix is not None else bone_matrix
        return self.calc_matrix(bone.get_bone_parent(), matrix, inverse)

    def get_matrix(self):
        if self.matrix is None:
            # calculate matrix
            matrix = None
            for bone in self.bone_weights:
                weight = self.bone_weights[bone]
                if matrix is None:
                    matrix = np.array(weight.bone.get_transform_matrix())
                    # self.rotation_matrix = get_rotation_matrix(matrix)
                    self.rotation_matrix = np.linalg.inv(get_rotation_matrix(matrix))
                    # matrix = np.dot(rotation_matrix_to_transform(self.rotation_matrix), matrix)
                    # matrix = self.calc_matrix(weight.bone)
                    # mtx = scale_matrix(np.identity(4), scale)
                    # matrix = translate_matrix(mtx, matrix[:, 3])
                else:
                    matrix = np.dot(matrix, weight.bone.get_transform_matrix())
            self.matrix = matrix
        return self.matrix

    def get_rotation_matrix(self):
        return self.rotation_matrix

    def get_inv_matrix(self):
        if self.inv_matrix is None:
            self.inv_matrix = np.linalg.inv(self.get_matrix())
            self.rotation_matrix = np.linalg.inv(self.rotation_matrix)
        return self.inv_matrix

    def apply_to(self, vertex, decode=True):
        """Takes a vertex and apply influence, mixed influences are ignored"""
        if self.is_mixed():
            return vertex
        matrix = self.get_matrix() if decode else self.get_inv_matrix()
        return apply_matrix_single(matrix, vertex)

    def apply_to_all(self, vertices, decode=True):
        if self.is_mixed():
            return vertices
        matrix = self.get_matrix() if decode else self.get_inv_matrix()
        vertices = apply_matrix(matrix, vertices)
        # rotation_matrix = self.get_rotation_matrix()
        # for i in range(len(vertices)):
        #     vertices[i] = np.dot(rotation_matrix, vertices[i])
        return vertices

    def is_mixed(self):
        return len(self.bone_weights) > 1

    def get_single_bone_bind(self):
        for x in self.bone_weights:
            return self.bone_weights[x].bone

    def __len__(self):
        return len(self.bone_weights)

    def __iter__(self):
        return iter(self.bone_weights)

    def __next__(self):
        return next(self.bone_weights)

    def __eq__(self, other):
        return self.bone_weights == other.bone_weights

    def __setitem__(self, key, value):
        self.bone_weights[key] = value

    def __getitem__(self, item):
        return self.bone_weights[item]


class Weight:
    """A single bone and weight pair"""

    def __init__(self, bone, weight):
        self.bone = bone
        self.weight = weight

    def __eq__(self, other):
        return self.bone == other.bone and self.weight == other.weight


class InfluenceCollection:
    def __init__(self, influences):
        """
        :param influences:  map of vertex indices to influences
        """
        self.influences = influences

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

    def is_mixed(self):
        return not (len(self.influences) == 1 and not self.influences[0].is_mixed())

    def get_single_bone_bind(self):
        for weight in self.influences[0]:
            return weight.bone

    def get_face_indices(self, vertex_face_indices):
        influences = self.influences
        return np.array([influences[vert].influence_id for vert in vertex_face_indices.flatten()]).reshape((-1, 3)) * 3


def decode_mdl0_influences(mdl0):
    influences = {}
    bones = mdl0.bones
    bonetable = mdl0.boneTable
    # Get bonetable influences
    for i in range(len(bonetable)):
        index = bonetable[i]
        if index >= 0:
            bone = bones[bonetable[index]]
            influences[i] = Influence(bone_weights={bone.name: Weight(bone, 1)}, influence_id=index)
    nodemix = mdl0.NodeMix
    if nodemix is not None:
        # for weight in nodemix.fixed_weights:
        #     weight_id = weight.weight_id
        #     bone = bones[bonetable[weight_id]]
        #     influences[weight_id] = Influence({bone.name: Weight(bone, 1)})
        for inf in nodemix.mixed_weights:
            weight_id = inf.weight_id
            influences[weight_id] = influence = Influence(influence_id=weight_id)
            for x in inf:
                bone = bones[bonetable[x[0]]]
                influence[bone.name] = Weight(bone, x[1])
    return InfluenceCollection(influences)


class InfluenceManager:
    """Manages all influences"""
    def __init__(self):
        self.mixed_influences = []      # influences with mixed weights
        self.single_influences = []     # influences with single weights

    def encode_bone_weights(self, mdl0):
        self.single_influences = sorted(self.single_influences, key=lambda x: x.get_single_bone_bind().index)
        self.__create_inf_ids()
        remaining_bones = self.__create_bone_table(mdl0)
        if self.mixed_influences:    # create node mix
            self.__create_node_mix(mdl0, remaining_bones)

    def create_or_find(self, influence):
        inf_list = self.mixed_influences if influence.is_mixed() else self.single_influences
        for x in inf_list:
            if x == influence:
                return x
        inf_list.append(influence)
        return influence

    def __create_node_mix(self, mdl0, remaining_bones):
        """Creates the mdl0 node mix"""
        node_mix = mdl0.NodeMix
        for x in self.single_influences:
            node_mix.add_fixed_weight(x.influence_id, x.get_single_bone_bind().index)
        for x in remaining_bones:
            node_mix.add_fixed_weight(x.weight_id, x.index)
        for inf in self.mixed_influences:
            node_mix.add_mixed_weight(inf.influence_id, [(x.bone.weight_id, x.weight) for x in inf.bone_weights.values()])
        return node_mix

    def __create_inf_ids(self):
        index = 0
        for x in self.single_influences:
            x.influence_id = index
            index += 1
        for x in self.mixed_influences:
            x.influence_id = index
            index += 1
        return index

    def __create_bone_table(self, mdl0):
        single_binds = [x.get_single_bone_bind() for x in self.single_influences]
        bonetable = []
        for i in range(len(single_binds)):
            bone = single_binds[i]
            bone.weight_id = i
            bonetable.append(bone.index)
        # influence ids for mixed
        mixed_length = len(self.mixed_influences)
        if mixed_length:
            bonetable += [-1] * mixed_length
        # now gather up remaining bones
        remaining = sorted([x for x in mdl0.bones if x not in single_binds], key=lambda x: x.index)
        index = len(bonetable)
        for x in remaining:
            bonetable.append(x.index)
            x.weight_id = index
            index += 1
        mdl0.set_bonetable(bonetable)
        return remaining
