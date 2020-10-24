from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile
from abmatt.brres.scn0 import light, fog, camera


def unpack_header(binfile):
    binfile.start()
    binfile.readLen()
    binfile.advance(4)  # ignore outer offset
    name = binfile.unpack_name()
    node_id, real_id = binfile.read('2I', 8)
    return name, node_id, real_id


class UnpackScn0(UnpackSubfile):
    class UnpackLight(Unpacker):
        def unpack(self, light, binfile):
            light.name, light.node_id, light.real_id = unpack_header(binfile)
            [light.non_spec_light_id] = binfile.read('I', 4)
            binfile.store()
            light.fixed_flags, light.usage_flags, light.vis_offset = binfile.read('2HI', 8)
            light.start_point = binfile.read('3f', 12)
            light.light_color = binfile.read('4B', 4)
            light.end_point = binfile.read('3f', 12)
            light.dist_func, light.ref_distance, light.ref_brightness = binfile.read('I2f', 12)
            light.spot_func, light.cutoff = binfile.read('If', 8)
            light.specular_color, light.shinyness = binfile.read('If', 8)
            binfile.end()

    class UnpackAmbientLight(Unpacker):
        def unpack(self, amb_light, binfile):
            amb_light.name, amb_light.node_id, amb_light.real_id = unpack_header(binfile)
            amb_light.fixed_flags, _, _, amb_light.flags = binfile.read('4B', 4)
            amb_light.lighting = binfile.read('4B', 4)
            binfile.end()

    class UnpackLightSet(Unpacker):
        def unpack(self, lightset, binfile):
            lightset.name, lightset.node_id, lightset.real_id = unpack_header(binfile)
            lightset.ambient_name = binfile.unpack_name()
            binfile.advance(2)
            [num_lights] = binfile.read('B', 2)
            next_offset = binfile.offset + 48
            binfile.start()
            for i in range(num_lights):
                lightset.light_names.append(binfile.unpack_name())  # check the offset
            binfile.end()
            # ignore the rest
            binfile.end()

    class UnpackFog(Unpacker):
        def unpack(self, fog, binfile):
            fog.name, fog.node_id, fog.real_id = unpack_header(binfile)
            # todo, key frames from start/end
            fog.flags, _, _, _, fog.type, fog.start, fog.end = binfile.read('4BI2f', 16)
            fog.color = binfile.read('4B', 4)
            binfile.end()

    class UnpackCamera(Unpacker):
        def unpack(self, camera, binfile):
            camera.name, camera.node_id, camera.real_id = unpack_header(binfile)
            camera.projection_type, camera.flags1, camera.flags2, udo = binfile.read('I2HI', 12)
            camera.position = binfile.read('3f', 12)
            camera.aspect, camera.near_z, camera.far_z = binfile.read('3f', 12)
            camera.rotate = binfile.read('3f', 12)
            camera.aim = binfile.read('3f', 12)
            camera.twist, camera.persp_fov_y, camera.ortho_height = binfile.read('3f', 12)
            binfile.end()

    def unpack_group(self, unpacker, klass, section_count):
        if self.binfile.recall():
            return [unpacker(klass(), self.binfile) for i in range(section_count)]
        return []

    def unpack(self, scn0, binfile):
        super().unpack(scn0, binfile)
        _, scn0.framecount, scn0.speclightcount, scn0.loop = binfile.read('i2Hi', 12)
        section_counts = binfile.read('5H', 12)  # + pad
        binfile.recall()  # section root
        # folder = Folder(binfile).unpack(binfile)
        # groups = [scn0.lightsets, scn0.ambient_lights, scn0.lights, scn0.fogs, scn0.cameras]
        scn0.lightsets = self.unpack_group(self.UnpackLightSet, light.LightSet, section_counts[0])
        scn0.ambient_lights = self.unpack_group(self.UnpackAmbientLight, light.AmbientLight, section_counts[1])
        scn0.lights = self.unpack_group(self.UnpackLight, light.Light, section_counts[2])
        scn0.fogs = self.unpack_group(self.UnpackFog, fog.Fog, section_counts[3])
        scn0.cameras = self.unpack_group(self.UnpackCamera, camera.Camera, section_counts[4])
        binfile.end()
