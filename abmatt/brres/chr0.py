"""CHR0 Subfile"""
from copy import copy

from abmatt.brres.lib.binfile import Folder
from abmatt.brres.subfile import SubFile, set_anim_str, get_anim_str


class Chr0(SubFile):
    """ Chr0 class representation """

    MAGIC = "CHR0"
    EXT = 'chr0'
    VERSION_SECTIONCOUNT = {5: 2, 3: 1}
    EXPECTED_VERSION = 5
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        self.animations = []
        super(Chr0, self).__init__(name, parent, binfile)

    def begin(self, initial_values=None):
        self.framecount = 1
        self.loop = True
        self.scaling_rule = 0

    class ModelAnim:
        def __init__(self, name, offset):
            self.name = name
            self.offset = offset  # since we don't parse data... store name offsetg

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def paste(self, item):
        self.framecount = item.framecount
        self.loop = item.loop
        self.data = copy(item.data)



    def unpack(self, binfile):
        self._unpack(binfile)
        _, self.framecount, num_entries, self.loop, self.scaling_rule = binfile.read('I2H2I', 16)
        binfile.recall()  # section 0
        f = Folder(binfile)
        f.unpack(binfile)
        self.data = binfile.readRemaining()
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
