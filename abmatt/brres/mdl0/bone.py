from copy import copy, deepcopy

import numpy as np

from abmatt.brres.lib.node import Node


class Bone(Node):
    """ Bone class """
    identity_matrix = ((1, 0, 0, 0),
                       (0, 1, 0, 0),
                       (0, 0, 1, 0))

    def __init__(self, name, parent, binfile=None, has_geometry=False,
                 scale_equal=True, fixed_scale=True,
                 fixed_rotation=True, fixed_translation=True):
        self.no_transform = False
        self.fixed_translation = fixed_translation
        self.fixed_rotation = fixed_rotation
        self.fixed_scale = fixed_scale
        self.scale_equal = scale_equal
        self.seg_scale_comp_apply = False
        self.seg_scale_comp_parent = False
        self.classic_scale_off = False
        self.visible = True
        self.has_geometry = has_geometry
        self.has_billboard_parent = False
        super().__init__(name, parent, binfile)

    def begin(self):
        self.index = 0
        self.weight_id = 0       # id in bone_table
        self.billboard = 0
        self.scale = (1, 1, 1)
        self.rotation = (0, 0, 0)
        self.translation = (0, 0, 0)
        self.minimum = (0, 0, 0)
        self.maximum = (0, 0, 0)
        self.b_parent = self.child = self.next = self.prev = None
        self.part2 = 0
        self.transform_matrix = [[y for y in x] for x in self.identity_matrix]
        self.inverse_matrix = [[y for y in x] for x in self.identity_matrix]

    def __deepcopy__(self, memodict={}):
        b = Bone(self.name, None)
        b.scale = copy(self.scale)
        b.rotation = copy(self.rotation)
        b.translation = copy(self.translation)
        b.minimum = copy(self.minimum)
        b.maximum = copy(self.maximum)
        b.child = deepcopy(self.child)
        b.part2 = self.part2
        b.transform_matrix = deepcopy(self.transform_matrix)
        b.inverse_matrix = deepcopy(self.inverse_matrix)
        b.no_transform = self.no_transform
        b.fixed_translation = self.fixed_translation
        b.fixed_scale = self.fixed_scale
        b.fixed_rotation = self.fixed_rotation
        b.scale_equal = self.scale_equal
        b.seg_scale_comp_apply = self.seg_scale_comp_apply
        b.seg_scale_comp_parent = self.seg_scale_comp_parent
        b.classic_scale_off = self.classic_scale_off
        b.visible = self.visible
        b.has_geometry = self.has_geometry
        b.has_billboard_parent = self.has_billboard_parent

    def __eq__(self, other):
        result = super().__eq__(other) and np.allclose(self.scale, other.scale) and \
               np.allclose(self.rotation, other.rotation) and np.allclose(self.translation, other.translation) and \
               np.allclose(self.transform_matrix, other.transform_matrix) and self.no_transform == other.no_transform \
               and self.fixed_translation == other.fixed_translation and self.fixed_scale == other.fixed_scale \
               and self.fixed_rotation == other.fixed_rotation and self.scale_equal == other.scale_equal and \
               self.seg_scale_comp_apply == other.seg_scale_comp_apply \
               and self.seg_scale_comp_parent == other.seg_scale_comp_parent \
               and self.classic_scale_off == other.classic_scale_off and self.visible == other.visible \
               and self.has_geometry == other.has_geometry and self.has_billboard_parent == other.has_billboard_parent
        return result

    def get_bone_parent(self):
        return self.b_parent

    def get_transform_matrix(self):
        matrix = [[y for y in x] for x in self.transform_matrix]
        matrix.append([0,0,0,1])
        return matrix

    def get_inv_transform_matrix(self):
        matrix = [[y for y in x] for x in self.inverse_matrix]
        matrix.append([0, 0, 0, 1])
        return matrix

    def set_translation(self, trans):
        self.translation = trans
        self.fixed_translation = self.no_transform = False
        for i in range(3):
            self.transform_matrix[i][2] = trans[i]
            self.inverse_matrix[i][2] = trans[i] * -1

    def get_children(self):
        if not self.child:
            return None
        children = []
        bone = self.child
        while bone:
            children.append(bone)
            bone = bone.next
        return children

    def link_child(self, child):
        if self.child:
            bone = self.child
            while True:
                if bone.next:
                    bone = bone.next
                else:
                    bone.next = child
                    child.prev = bone
                    break
        else:
            self.child = child
        child.b_parent = self

    def get_last_child(self):
        if self.child:
            bone = self.child
            while True:
                if bone.next:
                    bone = bone.next
                else:
                    return bone


