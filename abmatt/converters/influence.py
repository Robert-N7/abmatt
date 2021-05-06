import numpy as np

from abmatt.converters.matrix import apply_matrix_single, apply_matrix


class Joint:
    def __init__(self, name, matrix=None, parent=None):
        self.name = name
        self.matrix = matrix if matrix is not None else np.identity(4)
        self.children = None
        self.parent = parent

    def get_transform_matrix(self):
        return self.matrix

    def get_inv_transform_matrix(self):
        return np.linalg.inv(self.matrix)

    def get_bone_parent(self):
        return self.parent

    @staticmethod
    def get_world_position(bone):
        matrix = bone.get_inv_transform_matrix()
        parent = bone.get_bone_parent()
        if parent is not None:
            return np.dot(matrix, Joint.get_world_position(parent))
        return matrix


class Influence:
    """
    Influence is used for skins to determine how bones effect vertices
    An influence consists of a number of bone weights, the bone matrices
    are combined using their corresponding weights to get a transformation matrix,
    which is applied to the vertices.
    """

    def __init__(self, bone_weights=None, influence_id=None, matrix=None):
        self.bone_weights = {} if bone_weights is None else bone_weights
        self.world_matrix = self.matrix = self.inv_matrix = matrix
        self.influence_id = influence_id

    def __str__(self):
        return str(self.bone_weights)

    # def calc_matrix(self, bone, matrix=None, inverse=False):
    #     if bone is None:
    #         return matrix
    #     bone_matrix = bone.get_transform_matrix() if not inverse else bone.get_inv_transform_matrix()
    #     matrix = np.dot(bone_matrix, matrix) if matrix is not None else bone_matrix
    #     return self.calc_matrix(bone.get_bone_parent(), matrix, inverse)

    def __get_transformation_bind(self, bone):
        # translation = np.array(bone.get_transform_matrix())[:3, 3]
        parent = bone.get_bone_parent()
        if parent:
            transform = self.__get_transformation_bind(parent)
            # translation += transform
            # return tb ranslation
            return np.dot(transform, np.array(bone.get_transform_matrix()))
        return np.array(bone.get_transform_matrix())

    def get_matrix(self):
        if self.matrix is None:
            # calculate matrix
            matrix = None
            for bone in self.bone_weights:
                weight = self.bone_weights[bone]
                if matrix is None:
                    matrix = np.array(weight.bone.get_transform_matrix())
                else:
                    raise NotImplementedError()
            self.matrix = matrix
        return self.matrix

    # def get_rotation_matrix(self):
    #     return self.rotation_matrix

    def get_inv_matrix(self):
        if self.inv_matrix is None:
            self.inv_matrix = np.linalg.inv(self.get_matrix())
            # self.rotation_matrix = np.linalg.inv(self.rotation_matrix)
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
        return vertices

    def __get_world_position_matrix(self):
        if self.world_matrix is None:
            matrix = None
            for bone in self.bone_weights:
                bone_weight = self.bone_weights[bone]
                bw_matrix = Joint.get_world_position(bone_weight.bone) * bone_weight.weight
                if matrix is None:
                    matrix = bw_matrix
                else:
                    matrix = np.dot(matrix, bw_matrix)
            self.world_matrix = matrix
        return self.world_matrix

    def apply_world_position(self, vertex):
        return apply_matrix_single(self.__get_world_position_matrix(), vertex)

    def apply_world_position_all(self, vertices):
        return apply_matrix(self.__get_world_position_matrix(), vertices)

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

    def __str__(self):
        return str((self.bone.name, self.weight))

    def __eq__(self, other):
        return self.bone.name == other.bone.name and np.allclose(self.weight, other.weight, 1e-3)


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
        if not self.is_mixed():
            return self.influences[0].get_single_bone_bind()

    def apply_world_position(self, vertices):
        if len(self.influences) < len(vertices):
            influence = self.influences[0]
            influence.apply_world_position_all(vertices)
        else:
            for i in range(len(vertices)):
                influence = self.influences[i]
                influence.apply_world_position(vertices[i])

    def get_weighted_tri_groups(self, tri_face_points):
        """
        Get the WeightedTriGroups corresponding to the tri_face_points
        """
        influences = self.influences
        tris = [WeightedTri(x, [influences[x[i][0]] for i in range(3)]) for x in tri_face_points]
        # construct the groups
        groups = [WeightedTriGroup()]
        for x in tris:
            added = False
            for group in groups:
                if group.try_adding(x):
                    added = True
                    break
            if not added:
                group = WeightedTriGroup([x])
                groups.append(group)
        return groups


class WeightedTri:
    def __init__(self, tripoints, influences):
        # self.vertices = [x[0] for x in tripoints]
        self.tripoints = tripoints
        self.influences = influences


class WeightedTriGroup:
    """Represents a set of weighted triangles with a maximum of 10 influences"""
    MAX_INFLUENCES = 10  # can only have 10 matrices max

    def __init__(self, triangles=None):
        self.triangles = []
        self.influences = set()
        self.matrices = None
        if triangles is not None:
            for x in triangles:
                self.try_adding(x)

    def try_adding(self, triangle):
        """
        Tries to add the weighted triangle to the group by determining if the corresponding influences
        will be too much to hold in the group
        :param triangle: weighted triangle
        :return: True on success
        """
        need_adding = {inf.influence_id for inf in triangle.influences if inf.influence_id not in self.influences}
        if len(need_adding) + len(self.influences) > self.MAX_INFLUENCES:
            return False
        for x in need_adding:
            self.influences.add(x)
        self.triangles.append(triangle)
        return True

    def get_influence_indices(self):
        """
        Gets the influence indices (matrices) and the facepoint indexer for the triangles
        :return: influence indices,  np array shape (n, 3, 2)
        """
        matrices = []
        remapper = {}
        for inf in self.influences:
            remapper[inf] = len(matrices) * 3
            matrices.append(inf)

        # now construct facepoints
        facepoint_indexer = []
        for triangle in self.triangles:
            tri = []
            for i in range(3):  # each tri point
                tri.append((remapper[triangle.influences[i].influence_id], *triangle.tripoints[i]))
            facepoint_indexer.append(tri)
        return matrices, np.array(facepoint_indexer, np.uint)


class InfluenceManager:
    """Manages all influences"""

    def __init__(self, influence_collection=None):
        self.mixed_influences = []  # influences with mixed weights
        self.single_influences = []  # influences with single weights
        if influence_collection:
            for x in influence_collection:
                inf = influence_collection[x]
                if inf.is_mixed():
                    self.mixed_influences.append(inf)
                else:
                    self.single_influences.append(inf)

    def encode_bone_weights(self, mdl0):
        bone_sorted_single_bind_infs = sorted(self.single_influences, key=lambda x: x.get_single_bone_bind().index)
        self.__create_inf_ids(bone_sorted_single_bind_infs)
        bones_with_infs = [x.get_single_bone_bind() for x in bone_sorted_single_bind_infs]
        remaining_bones = self.__create_bone_table(mdl0, bones_with_infs)
        if self.mixed_influences:  # create node mix
            bones_to_infs = {}
            for x in bone_sorted_single_bind_infs:
                bones_to_infs[x.get_single_bone_bind().index] = x
            self.__create_node_mix(mdl0, remaining_bones, bones_to_infs)

    def create_or_find(self, influence):
        inf_list = self.mixed_influences if influence.is_mixed() else self.single_influences
        for x in inf_list:
            if x == influence:
                return x
        inf_list.append(influence)
        return influence

    def __create_node_mix(self, mdl0, remaining_bones, bones_to_infs):
        """Creates the mdl0 node mix"""
        node_mix = mdl0.NodeMix
        used_weights = set()
        for inf in self.mixed_influences:
            for x in inf.bone_weights.values():
                used_weights.add(x.bone.weight_id)
            node_mix.add_mixed_weight(inf.influence_id,
                                      [(x.bone.weight_id, x.weight) for x in inf.bone_weights.values()])
        for bone in mdl0.bones:
            if bone not in remaining_bones:
                weight_id = bones_to_infs[bone.index].influence_id
            else:
                weight_id = bone.weight_id
            if weight_id in used_weights:
                node_mix.add_fixed_weight(weight_id, bone.index)
        return node_mix

    def __create_inf_ids(self, bone_sorted_singles):
        index = 0
        for x in bone_sorted_singles:
            x.influence_id = index
            index += 1
        for x in self.mixed_influences:
            x.influence_id = index
            index += 1
        return index

    def __create_bone_table(self, mdl0, single_binds):
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
