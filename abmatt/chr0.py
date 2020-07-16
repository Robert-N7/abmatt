"""CHR0 Subfile"""
from abmatt.subfile import SubFile
from abmatt.binfile import Folder, printCollectionHex


class Chr0(SubFile):
    """ Chr0 class representation """
    MAGIC = "CHR0"
    VERSION_SECTIONCOUNT = {5: 2, 3: 1}
    EXPECTED_VERSION = 5
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent):
        super(Chr0, self).__init__(name, parent)
        self.animations = []
        self.framecount = 1
        self.loop = True

    def __getitem__(self, item):
        if item == self.SETTINGS[0]:
            return self.framecount
        elif item == self.SETTINGS[1]:
            return self.loop

    class ModelAnim:
        def __init__(self, name, offset):
            self.name = name
            self.offset = offset  # since we don't parse data... store name offsetg

    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.framecount, num_entries, self.loop, self.scaling_rule = binfile.read('I2H2I', 16)
        binfile.recall()  # section 0
        f = Folder(binfile)
        f.unpack(binfile)
        self.data = binfile.readRemaining(self.byte_len)
        # printCollectionHex(self.data)
        while len(f):
            name = f.recallEntryI()
            self.animations.append(self.ModelAnim(name, binfile.offset - binfile.beginOffset))

    def pack(self, binfile):
        self._pack(binfile)
        binfile.write('I2H2I', 0, self.framecount, len(self.animations), self.loop, self.scaling_rule)
        f = Folder(binfile)
        for x in self.animations:
            f.addEntry(x.name)
        binfile.createRef()
        f.pack(binfile)
        binfile.writeRemaining(self.data)
        for x in self.animations:  # hackish way of overwriting the string offsets
            binfile.offset = binfile.beginOffset + x.offset
            f.createEntryRefI()
            binfile.storeNameRef(x.name)
        binfile.end()
