from copy import deepcopy

from abmatt.brres.lib.binfile import Folder, printCollectionHex
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_key_frames import unpack_key_frames, unpack_frame_lists
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile


class UnpackChr0(UnpackSubfile):
    def unpack(self, chr0, binfile):
        super().unpack(chr0, binfile)
        _, chr0.framecount, num_entries, chr0.loop, chr0.scaling_rule = binfile.read('I2H2I', 16)
        binfile.recall()  # section 0 (animation data)
        f = Folder(binfile)
        f.unpack(binfile)
        chr0.data = binfile.readRemaining()
        while len(f):
            name = f.recallEntryI()
            bone_anim = chr0.BoneAnimation(name, self.node, binfile, chr0.framecount, chr0.loop)
            bone_anim.offset = binfile.offset - binfile.beginOffset
            # UnpackChr0BoneAnim(bone_anim, binfile)
            chr0.animations.append(bone_anim)
            # chr0.animations.append(chr0.BoneAnimation(name, binfile.offset - binfile.beginOffset))
        binfile.end()


class UnpackChr0BoneAnim(Unpacker):
    def unpack(self, node, binfile):
        binfile.start()
        # Unpack Code
        name = binfile.unpack_name()
        [code] = binfile.read('I', 4)
        no_srt = bool(code & 0x2)        # scale 1 rotation 0 translation 0
        rotation_translation_0 = bool(code & 0x4)      # rotation 0 translation 0
        scale_one = bool(code & 0x8)     # scale 1
        scale_isotropic = bool(code & 0x10)
        rotation_isotropic = bool(code & 0x20)
        translation_isotropic = bool(code & 0x40)
        use_model_scale = bool(code & 0x80)
        use_model_rotation = bool(code & 0x100)
        use_model_translation = bool(code & 0x200)
        node.scale_comp_apply = bool(code & 0x400)
        node.scale_comp_parent = bool(code & 0x800)
        node.classic_scale_off = bool(code & 0x1000)
        x_scale_fixed = bool(code & 0x2000)
        y_scale_fixed = bool(code & 0x4000)
        z_scale_fixed = bool(code & 0x8000)
        code >>= 16

        x_rotation_fixed = bool(code & 0x1)
        y_rotation_fixed = bool(code & 0x2)
        z_rotation_fixed = bool(code & 0x4)
        code >>= 3
        x_translation_fixed = bool(code & 0x1)
        y_translation_fixed = bool(code & 0x2)
        z_translation_fixed = bool(code & 0x4)
        code >>= 3
        scale_exists = bool(code & 0x1)
        rotation_exists = bool(code & 0x2)
        translation_exists = bool(code & 0x4)
        node.scale_format = code >> 3 & 3
        node.rotation_format = code >> 5 & 7
        node.translation_format = code >> 8 & 3
        print(f'scale format {node.scale_format} rot format {node.rotation_format} trans format {node.translation_format}')

        # Now unpack entries
        unpack_frame_lists(binfile, (node.x_scale, node.y_scale, node.z_scale),
                           scale_exists, scale_isotropic,
                           (x_scale_fixed, y_scale_fixed, z_scale_fixed))
        unpack_frame_lists(binfile, (node.x_rotation, node.y_rotation, node.z_rotation),
                           rotation_exists, rotation_isotropic,
                           (x_rotation_fixed, y_rotation_fixed, z_rotation_fixed))
        unpack_frame_lists(binfile, (node.x_translation, node.y_translation, node.z_translation),
                           translation_exists, translation_isotropic,
                           (x_translation_fixed, y_translation_fixed, z_translation_fixed))
        binfile.end()
        return node


