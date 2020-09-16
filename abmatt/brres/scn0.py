"""SCN0 Subfile"""
from copy import deepcopy

from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str
from abmatt.brres.lib.binfile import Folder


def unpack_header(binfile):
    binfile.start()
    binfile.readLen()
    binfile.advance(4)  # ignore outer offset
    name = binfile.unpack_name()
    node_id, real_id = binfile.read('2I', 8)
    return name, node_id, real_id


def pack_header(binfile, name, node_id, real_id):
    binfile.start()
    binfile.markLen()
    binfile.write('i', binfile.getOuterOffset())
    binfile.storeNameRef(name)
    binfile.write('2I', node_id, real_id)


class LightSet:
    def __init__(self):
        self.light_names = []

    def unpack(self, binfile):
        self.name, self.node_id, self.real_id = unpack_header(binfile)
        self.ambient_name = binfile.unpack_name()
        binfile.advance(2)
        [num_lights] = binfile.read('B', 2)
        next_offset = binfile.offset + 48
        binfile.start()
        for i in range(num_lights):
            self.light_names.append(binfile.unpack_name())  # check the offset
        binfile.end()
        # ignore the rest
        binfile.end()
        return self

    def pack(self, binfile):
        pack_header(binfile, self.name, self.node_id, self.real_id)
        binfile.storeNameRef(self.ambient_name)
        filler = 0xffff
        binfile.write('H', filler)
        binfile.write('B', len(self.light_names))
        binfile.advance(1)
        for x in self.light_names:
            binfile.storeNameRef(x)
        binfile.advance((8-len(self.light_names))*4)
        for i in range(8):
            binfile.write('H', filler)
        binfile.end()


class AmbientLight:
    def __init__(self):
        pass

    def unpack(self, binfile):
        self.name, self.node_id, self.real_id = unpack_header(binfile)
        self.fixed_flags, _, _, self.flags = binfile.read('4B', 4)
        self.lighting = binfile.read('4B', 4)
        binfile.end()
        return self

    def pack(self, binfile):
        pack_header(binfile, self.name, self.node_id, self.real_id)
        binfile.write('4B', self.fixed_flags, 0, 0, self.flags)
        binfile.write('4B', *self.lighting)
        binfile.end()


class Light:
    def __init__(self):
        pass

    def unpack(self, binfile):
        self.name, self.node_id, self.real_id = unpack_header(binfile)
        [self.non_spec_light_id] = binfile.read('I', 4)
        binfile.store()
        self.fixed_flags, self.usage_flags, self.vis_offset = binfile.read('2HI', 8)
        self.start_point = binfile.read('3f', 12)
        self.light_color = binfile.read('4B', 4)
        self.end_point = binfile.read('3f', 12)
        self.dist_func, self.ref_distance, self.ref_brightness = binfile.read('I2f', 12)
        self.spot_func, self.cutoff = binfile.read('If', 8)
        self.specular_color, self.shinyness = binfile.read('If', 8)
        binfile.end()
        return self

    def pack(self, binfile):
        pack_header(binfile, self.name, self.node_id, self.real_id)
        binfile.write('2I', self.non_spec_light_id, 0)
        binfile.write('2HI', self.fixed_flags, self.usage_flags, self.vis_offset)
        binfile.write('3f', *self.start_point)
        binfile.write('4B', *self.light_color)
        binfile.write('3f', *self.end_point)
        binfile.write('I2f', self.dist_func, self.ref_distance, self.ref_brightness)
        binfile.write('If', self.spot_func, self.cutoff)
        binfile.write('If', self.specular_color, self.shinyness)
        binfile.end()


class Fog:
    def __init__(self):
        pass

    def unpack(self, binfile):
        self.name, self.node_id, self.real_id = unpack_header(binfile)
        # todo, key frames from start/end
        self.flags, _, _, _, self.type, self.start, self.end = binfile.read('4BI2f', 16)
        self.color = binfile.read('4B', 4)
        binfile.end()
        return self

    def pack(self, binfile):
        print('WARNING: packing scn0 fog is not supported.')
        pack_header(binfile, self.name, self.node_id, self.real_id)
        binfile.write('4BI2f', self.flags, 0, 0, 0, self.type, self.start, self.end)
        binfile.write('4B', self.color)
        binfile.end()


class Camera:
    def __init__(self):
        pass

    def unpack(self, binfile):
        self.name, self.node_id, self.real_id = unpack_header(binfile)
        self.projection_type, self.flags1, self.flags2, udo = binfile.read('I2HI', 12)
        self.position = binfile.read('3f', 12)
        self.aspect, self.near_z, self.far_z = binfile.read('3f', 12)
        self.rotate = binfile.read('3f', 12)
        self.aim = binfile.read('3f', 12)
        self.twist, self.persp_fov_y, self.ortho_height = binfile.read('3f', 12)
        binfile.end()
        return self

    def pack(self, binfile):
        pack_header(binfile, self.name, self.node_id, self.real_id)
        binfile.write('I2HI', self.projection_type, self.flags1, self.flags2, 0)
        binfile.write('3f', *self.position)
        binfile.write('3f', self.aspect, self.near_z, self.far_z)
        binfile.write('3f', *self.rotate)
        binfile.write('3f', *self.aim)
        binfile.write('3f', self.twist, self.persp_fov_y, self.ortho_height)
        binfile.end()


class Scn0KeyFrameList:
    def __init__(self):
        self.frames = []

    class KeyFrame:
        def __init__(self, value=0, index=0, delta=0):
            self.value = value
            self.index = index
            self.delta = delta

        def unpack(self, binfile):
            self.delta, self.index, self.value = binfile.read('3f', 12)
            return self

        def pack(self, binfile):
            binfile.write('3f', self.delta, self.index, self.value)

    def unpack(self, binfile):
        num_entries, uk = binfile.read('2H', 4)
        for i in range(num_entries):
            self.frames.append(self.KeyFrame().unpack(binfile))
        return self

    def pack(self, binfile):
        binfile.write('2H', len(self.frames), 0)
        for x in self.frames:
            x.pack(binfile)


class Scn0(SubFile):
    MAGIC = "SCN0"
    EXT = 'scn0'
    VERSION_SECTIONCOUNT = {4: 6, 5: 7}
    EXPECTED_VERSION = 5
    SETTINGS = ('framecount', 'loop')
    FOLDERS = ('LightSet(NW4R)', 'AmbLights(NW4R)', 'Lights(NW4R)', 'Fog(NW4R)', 'Cameras(NW4R)')
    KLASSES = (LightSet, AmbientLight, Light, Fog, Camera)

    def __init__(self, name, parent, binfile=None):
        self.animations = []
        self.lightsets = []
        self.ambient_lights = []
        self.lights = []
        self.fogs = []
        self.cameras = []
        super(Scn0, self).__init__(name, parent, binfile)

    def begin(self):
        self.framecount = 1
        self.loop = True

    def __getitem__(self, item):
        if item == self.SETTINGS[0]:
            return self.framecount
        elif item == self.SETTINGS[1]:
            return self.loop

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.framecount = item.framecount
        self.loop = item.loop
        self.animations = deepcopy(item.animations)
        self.lightsets = deepcopy(item.lightsets)
        self.ambient_lights = deepcopy(item.ambient_lights)
        self.lights = deepcopy(item.lights)
        self.fogs = deepcopy(item.fogs)
        self.cameras = deepcopy(item.cameras)

    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.framecount, self.speclightcount, self.loop = binfile.read('i2Hi', 12)
        section_counts = binfile.read('5H', 12)  # + pad
        binfile.recall()    # section root
        # folder = Folder(binfile).unpack(binfile)
        groups = [self.lightsets, self.ambient_lights, self.lights, self.fogs, self.cameras]
        for i in range(5):
            n = section_counts[i]
            if binfile.recall():
                klass = self.KLASSES[i]
                folder = groups[i]
                for j in range(n):
                    folder.append(klass().unpack(binfile))
        binfile.end()

    def pack_root(self, binfile, packing_items):
        binfile.createRef() # section root
        root = Folder(binfile)
        index_groups = []
        for i in range(5):
            if packing_items[i]:
                root.addEntry(self.FOLDERS[i])
                f = Folder(binfile, self.FOLDERS[i])
                index_groups.append(f)
                for item in packing_items[i]:
                    f.addEntry(item.name)
        root.pack(binfile)
        for x in index_groups:
            root.createEntryRefI()
            x.pack(binfile) # doesn't create data pointers
        return index_groups

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('i2Hi', 0, self.framecount, self.speclightcount, self.loop)
        packing_items = [self.lightsets, self.ambient_lights, self.lights, self.fogs, self.cameras]
        # write counts
        binfile.write('5H', *[len(x) for x in packing_items])
        folders = self.pack_root(binfile, packing_items)
        # all the rest
        for i in range(5):
            group = packing_items[i]
            if len(group):
                binfile.createRef(i, False) # create section header offset
                folder = folders.pop(0)
                for x in group:
                    folder.createEntryRefI()
                    x.pack(binfile)
        binfile.end()
