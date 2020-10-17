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



# class BoneTable:
#     """ Bonetable class """
#     def __init__(self, binfile=None):
#         if binfile:
#             self.unpack(binfile)
#         else:
#             self.entries = []
#
#     def __getitem__(self, item):
#         return self.entries[item]
#
#     def __len__(self):
#         return len(self.entries)
#
#     def add_entry(self, entry):
#         self.entries.append(entry)
#         return len(self.entries) - 1
#
#
#     def pack(self, binfile):
#         length = len(self.entries)
#         binfile.write("I", length)
#         binfile.write("{}i".format(length), *self.entries)
