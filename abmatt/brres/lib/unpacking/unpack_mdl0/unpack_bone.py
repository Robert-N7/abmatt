from abmatt.lib.unpack_interface import Unpacker
from abmatt.brres.mdl0.bone import Bone


def unpack_bonetable(binfile, format):
    [length] = binfile.read("I", 4)
    if length:
        return binfile.read("{}{}".format(length, format), length * 4)


class UnpackBone(Unpacker):
    def __init__(self, name, parent, binfile):
        super().__init__(Bone(name, parent, binfile), binfile)

    def find_bone_at(self, offset, bones):
        if offset:
            offset += self.offset
            for x in bones:
                if x.offset == offset:
                    return x.node
            raise ValueError('Failed to find bone link to {}'.format(offset))

    def post_unpack(self, unpackers):
        node = self.node
        node.b_parent = self.find_bone_at(self.b_parent, unpackers)
        node.child = self.find_bone_at(self.child, unpackers)
        node.next = self.find_bone_at(self.next, unpackers)
        node.prev = self.find_bone_at(self.prev, unpackers)

    def __parse_flags(self, node, flags):
        node.no_transform = flags & 1 != 0
        node.fixed_translation = flags & 0x2 != 0
        node.fixed_rotation = flags & 0x4 != 0
        node.fixed_scale = flags & 0x8 != 0
        node.scale_equal = flags & 0x10 != 0
        node.seg_scale_comp_apply = flags & 0x20 != 0
        node.seg_scale_comp_parent = flags & 0x40 != 0
        node.classic_scale_off = flags & 0x80 != 0
        node.visible = flags & 0x100 != 0
        node.has_geometry = flags & 0x200 != 0
        node.has_billboard_parent = flags & 0x400 != 0

    def unpack(self, bone, binfile):
        self.offset = binfile.start()
        binfile.read_len()
        binfile.advance(8)
        bone.index, bone.weight_id, flags, bone.billboard = binfile.read('4I', 20)
        self.__parse_flags(bone, flags)
        bone.scale = binfile.read('3f', 12)
        bone.rotation = binfile.read('3f', 12)
        bone.translation = binfile.read('3f', 12)
        bone.minimum = binfile.read('3f', 12)
        bone.maximum = binfile.read('3f', 12)
        self.b_parent, self.child, self.next, self.prev, bone.part2 = binfile.read('5i', 20)
        bone.transform_matrix = binfile.read_matrix(4, 3)
        bone.inverse_matrix = binfile.read_matrix(4, 3)
        binfile.end()
