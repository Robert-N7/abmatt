from abmatt.brres.lib.packing.interface import Packer


class PackBone(Packer):
    def __init__(self, node, binfile, index):
        self.index = index
        super().__init__(node, binfile)

    def __get_flags(self, bone):
        return bone.no_transform | bone.fixed_translation << 1 | bone.fixed_rotation << 2 \
               | bone.fixed_scale << 3 | bone.scale_equal << 4 | bone.seg_scale_comp_apply << 5 \
               | bone.seg_scale_comp_parent << 6 | bone.classic_scale_off << 7 | bone.visible << 8 \
               | bone.has_geometry << 9 | bone.has_billboard_parent << 10

    def pack(self, bone, binfile):
        bone.offset = binfile.start()
        # take care of marked references
        if bone.prev:
            binfile.createRefFrom(bone.prev.offset, 1)
        elif bone.b_parent:     # first child
            binfile.createRefFrom(bone.b_parent.offset, 0, False)
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.storeNameRef(bone.name)
        binfile.write('5I', self.index, bone.weight_id, self.__get_flags(bone), bone.billboard, 0)
        binfile.write('3f', *bone.scale)
        binfile.write('3f', *bone.rotation)
        binfile.write('3f', *bone.translation)
        binfile.write('3f', *bone.minimum)
        binfile.write('3f', *bone.maximum)
        binfile.write('i', bone.b_parent.offset - bone.offset) if bone.b_parent else binfile.advance(4)
        binfile.mark(2)     # mark child and next
        binfile.write('i', bone.prev.offset - bone.offset) if bone.prev else binfile.advance(4)
        binfile.write('i', bone.part2)
        binfile.writeMatrix(bone.transform_matrix)
        binfile.writeMatrix(bone.inverse_matrix)
        binfile.end()
