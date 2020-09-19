"""SHP0 """
from copy import deepcopy

from abmatt.brres.lib.binfile import Folder
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


class Shp0KeyFrameList:
    def __init__(self, id):
        self.frames = []
        self.id = id

    class Shp0KeyFrame:
        def __init__(self, frame_id, value, delta):
            self.frame_id = frame_id
            self.value = value
            self.delta = delta

    def unpack(self, binfile):
        num_entries, self.uk = binfile.read('2H', 4)
        for i in range(num_entries):
            data = binfile.read('3f', 12)
            self.frames.append(self.Shp0KeyFrame(data[1], data[2], data[0]))
        return self

    def pack(self, binfile):
        binfile.createRefFromStored()  # create the reference to this offset
        frames = self.frames
        binfile.write('2H', len(frames), self.uk)
        for frame in frames:
            binfile.write('3f', frame.delta, frame.frame_id, frame.value)


class Shp0Animation:
    """A single animation entry in the file"""
    def __init__(self, name):
        # for modifying, need to add framecount / texture references .. etc
        self.name = name
        self.entries = []

    def unpack(self, binfile):
        binfile.start()
        [self.flags] = binfile.read('I', 4)
        binfile.advance(4)  # name
        self.name_id, num_entries, self.fixed_flags, indices_offset = binfile.read('2H2i', 12)
        self.indices = binfile.read('{}H'.format(num_entries), num_entries * 2)
        binfile.offset = indices_offset + binfile.beginOffset - 4 * num_entries
        for i in range(num_entries):
            shp = Shp0KeyFrameList(self.indices[i])
            binfile.bl_unpack(shp.unpack, False)
            self.entries.append(shp)
        binfile.end()
        return self

    def pack(self, binfile):
        binfile.start()
        binfile.write('I', self.flags)
        binfile.storeNameRef(self.name)
        entries = self.entries
        binfile.write('2Hi', self.name_id, len(entries), self.fixed_flags)
        binfile.mark()  # indices offset
        binfile.align(4)
        binfile.mark(len(entries))
        binfile.createRef() # indices offset
        binfile.write('{}H'.format(len(entries)), *self.indices)
        for x in entries:
            x.pack(binfile)
        binfile.end()


class Shp0(SubFile):

    MAGIC = "SHP0"
    EXT = 'shp0'
    VERSION_SECTIONCOUNT = {4: 3, 3: 2}
    EXPECTED_VERSION = 4
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        self.framecount = 1
        self.loop = True
        self.animations = []
        self.strings = []
        super(Shp0, self).__init__(name, parent, binfile)

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
        self.strings = deepcopy(item.strings)

    def unpack(self, binfile):
        # print('{} Warning: Shp0 not supported, unable to edit'.format(self.parent.name))
        self._unpack(binfile)
        orig_path, self.framecount, num_anim, self.loop = binfile.read('I2HI', 12)
        binfile.recall(1)  # Section 1 string list
        binfile.start()
        for i in range(num_anim):
            self.strings.append(binfile.unpack_name())
        binfile.end()
        binfile.recall()  # Section 0 Data
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            self.animations.append(Shp0Animation(folder.recallEntryI()).unpack(binfile))
        binfile.end()
        # self._unpackData(binfile)

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I2HI', 0, self.framecount, len(self.strings), self.loop)
        binfile.createRef()     # section 0
        folder = Folder(binfile)
        for x in self.animations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        for x in self.animations:
            folder.createEntryRefI()
            x.pack(binfile)
        binfile.createRef()     # section 1
        binfile.start()
        for x in self.strings:
            binfile.storeNameRef(x)
        binfile.end()
        binfile.end()
