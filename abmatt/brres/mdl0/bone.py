from abmatt.brres.lib.node import Node


class Bone(Node):
    """ Bone class """
    identity_matrix = ((1, 0, 0, 0),
                       (0, 1, 0, 0),
                       (0, 0, 1, 0))

    def __init__(self, name, parent, binfile=None, has_geometry=True,
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
        self.bone_id = 0       # id in bone_table
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

    def __parse_flags(self, flags):
        self.no_transform = flags & 1 != 0
        self.fixed_translation = flags & 0x2 != 0
        self.fixed_rotation = flags & 0x4 != 0
        self.fixed_scale = flags & 0x8 != 0
        self.scale_equal = flags & 0x10 != 0
        self.seg_scale_comp_apply = flags & 0x20 != 0
        self.seg_scale_comp_parent = flags & 0x40 != 0
        self.classic_scale_off = flags & 0x80 != 0
        self.visible = flags & 0x100 != 0
        self.has_geometry = flags & 0x200 != 0
        self.has_billboard_parent = flags & 0x400 != 0

    def __get_flags(self):
        return self.no_transform | self.fixed_translation << 1 | self.fixed_rotation << 2 \
            | self.fixed_scale << 3 | self.scale_equal << 4 | self.seg_scale_comp_apply << 5 \
            | self.seg_scale_comp_parent << 6 | self.classic_scale_off << 7 | self.visible << 8 \
            | self.has_geometry << 9 | self.has_billboard_parent << 10

    def unpack(self, binfile):
        self.offset = binfile.start()
        binfile.readLen()
        binfile.advance(8)
        self.index, self.bone_id, flags, self.billboard = binfile.read('4I', 20)
        self.__parse_flags(flags)
        self.scale = binfile.read('3f', 12)
        self.rotation = binfile.read('3f', 12)
        self.translation = binfile.read('3f', 12)
        self.minimum = binfile.read('3f', 12)
        self.maximum = binfile.read('3f', 12)
        self.b_parent, self.child, self.next, self.prev, self.part2 = binfile.read('5i', 20)
        self.transform_matrix = binfile.readMatrix(4, 3)
        self.inverse_matrix = binfile.readMatrix(4, 3)
        binfile.end()

    def find_bone_at(self, offset, bones):
        if offset:
            offset += self.offset
            for x in bones:
                if x.offset == offset:
                    return x
            raise ValueError('Failed to find bone link to {}'.format(offset))

    @staticmethod
    def post_unpack(bones):
        for b in bones:
            b.b_parent = b.find_bone_at(b.b_parent, bones)
            b.child = b.find_bone_at(b.child, bones)
            b.next = b.find_bone_at(b.next, bones)
            b.prev = b.find_bone_at(b.prev, bones)


    def pack(self, binfile):
        self.offset = binfile.start()
        # take care of marked references
        if self.prev:
            binfile.createRefFrom(self.prev.offset, 1)
        elif self.b_parent:     # first child
            binfile.createRefFrom(self.b_parent.offset, 0, False)
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.storeNameRef(self.name)
        binfile.write('5I', self.index, self.bone_id, self.__get_flags(), self.billboard, 0)
        binfile.write('3f', *self.scale)
        binfile.write('3f', *self.rotation)
        binfile.write('3f', *self.translation)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        binfile.write('i', self.b_parent.offset - self.offset) if self.b_parent else binfile.advance(4)
        binfile.mark(2)     # mark child and next
        binfile.write('i', self.prev.offset - self.offset) if self.prev else binfile.advance(4)
        binfile.write('i', self.part2)
        binfile.writeMatrix(self.transform_matrix)
        binfile.writeMatrix(self.inverse_matrix)
        binfile.end()


class BoneTable:
    """ Bonetable class """
    def __init__(self, binfile=None):
        if binfile:
            self.unpack(binfile)
        else:
            self.entries = []

    def __getitem__(self, item):
        return self.entries[item]

    def __len__(self):
        return len(self.entries)

    def add_entry(self, entry):
        self.entries.append(entry)
        return len(self.entries) - 1

    def unpack(self, binfile):
        """ unpacks bonetable """
        [length] = binfile.read("I", 4)
        self.entries = binfile.read("{}i".format(length), length * 4)

    def pack(self, binfile):
        length = len(self.entries)
        binfile.write("I", length)
        binfile.write("{}i".format(length), *self.entries)
