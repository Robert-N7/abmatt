from abmatt.autofix import AutoFix
from abmatt.lib.binfile import Folder
from abmatt.lib.pack_interface import Packer
from abmatt.brres.lib.packing.pack_subfile import PackSubfile


def pack_header(binfile, name, node_id, real_id):
    binfile.start()
    binfile.mark_len()
    binfile.write_outer_offset()
    binfile.store_name_ref(name)
    binfile.write('2I', node_id, real_id)


class PackScn0(PackSubfile):
    class PackLight(Packer):
        def pack(self, light, binfile):
            pack_header(binfile, light.name, light.node_id, light.real_id)
            binfile.write('2I', light.non_spec_light_id, 0)
            binfile.write('2HI', light.fixed_flags, light.usage_flags, light.vis_offset)
            binfile.write('3f', *light.start_point)
            binfile.write('4B', *light.light_color)
            binfile.write('3f', *light.end_point)
            binfile.write('I2f', light.dist_func, light.ref_distance, light.ref_brightness)
            binfile.write('If', light.spot_func, light.cutoff)
            binfile.write('If', light.specular_color, light.shinyness)
            binfile.end()

    class PackAmbientLight(Packer):
        def pack(self, ambient_light, binfile):
            pack_header(binfile, ambient_light.name, ambient_light.node_id, ambient_light.real_id)
            binfile.write('4B', ambient_light.fixed_flags, 0, 0, ambient_light.flags)
            binfile.write('4B', *ambient_light.lighting)
            binfile.end()

    class PackLightSet(Packer):
        def pack(self, lightset, binfile):
            pack_header(binfile, lightset.name, lightset.node_id, lightset.real_id)
            binfile.store_name_ref(lightset.ambient_name)
            filler = 0xffff
            binfile.write('H', filler)
            binfile.write('B', len(lightset.light_names))
            binfile.advance(1)
            binfile.start()
            for x in lightset.light_names:
                binfile.store_name_ref(x)
            binfile.end()
            binfile.advance((8 - len(lightset.light_names)) * 4)
            for i in range(8):
                binfile.write('H', filler)
            binfile.end()

    class PackFog(Packer):
        def pack(self, fog, binfile):
            AutoFix.warn('packing scn0 fog is not supported.')
            pack_header(binfile, fog.name, fog.node_id, fog.real_id)
            binfile.write('4BI2f', fog.flags, 0, 0, 0, fog.type, fog.start, fog.end)
            binfile.write('4B', fog.color)
            binfile.end()

    class PackCamera(PackSubfile):
        def pack(self, camera, binfile):
            pack_header(binfile, camera.name, camera.node_id, camera.real_id)
            binfile.write('I2HI', camera.projection_type, camera.flags1, camera.flags2, 0)
            binfile.write('3f', *camera.position)
            binfile.write('3f', camera.aspect, camera.near_z, camera.far_z)
            binfile.write('3f', *camera.rotate)
            binfile.write('3f', *camera.aim)
            binfile.write('3f', camera.twist, camera.persp_fov_y, camera.ortho_height)
            binfile.end()

    def pack_root(self, scn0, binfile, packing_items):
        binfile.create_ref()  # section root
        root = Folder(binfile)
        index_groups = []
        for i in range(5):
            if packing_items[i]:
                root.add_entry(scn0.FOLDERS[i])
                f = Folder(binfile, scn0.FOLDERS[i])
                index_groups.append(f)
                for item in packing_items[i]:
                    f.add_entry(item.name)
        root.pack(binfile)
        for x in index_groups:
            root.create_entry_ref_i()
            x.pack(binfile)  # doesn't create data pointers
        return index_groups

    def pack_group(self, group, folders, packer_klass, parent_offset_index):
        if len(group):
            self.binfile.create_ref(parent_offset_index, False)  # create section header offset
            folder = folders.pop(0)
            for x in group:
                folder.create_entry_ref_i()
                packer_klass(x, self.binfile)

    def pack(self, scn0, binfile):
        super().pack(scn0, binfile)
        binfile.write('i2Hi', 0, scn0.framecount, scn0.speclightcount, scn0.loop)
        packing_items = [scn0.lightsets, scn0.ambient_lights, scn0.lights, scn0.fogs, scn0.cameras]
        # write counts
        binfile.write('5H', *[len(x) for x in packing_items])
        folders = self.pack_root(scn0, binfile, packing_items)
        # all the rest
        self.pack_group(scn0.lightsets, folders, self.PackLightSet, 0)
        self.pack_group(scn0.ambient_lights, folders, self.PackAmbientLight, 1)
        self.pack_group(scn0.lights, folders, self.PackLight, 2)
        self.pack_group(scn0.fogs, folders, self.PackFog, 3)
        self.pack_group(scn0.cameras, folders, self.PackCamera, 4)
        binfile.end()
