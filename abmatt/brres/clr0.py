"""CLR0 BRRES SUBFILE"""
from copy import deepcopy

from brres.subfile import SubFile, get_anim_str, set_anim_str
from brres.lib.binfile import Folder


class Clr0Animation:

    def __init__(self, name, framecount=1, loop=True):
        self.name = name
        self.framecount = framecount
        self.loop=loop
        self.flags = [False] * 16
        self.is_constant = [False] * 16
        self.entry_masks = []
        self.entries = []   # can be fixed (if constant) otherwise key frame list

    def unpack_flags(self, int_val):
        bit = 1
        for i in range(len(self.flags)):
            if int_val & bit:
                self.flags[i] = True
            bit <<= 1
            if int_val & bit:
                self.is_constant[i] = True
            bit <<= 1
        return self.flags, self.is_constant

    def pack_flags(self):
        bit = 1
        ret = 0
        for i in range(len(self.flags)):
            if self.flags[i]:
                ret |= bit
            bit <<= 1
            if self.is_constant[i]:
                ret |= bit
            bit <<= 1
        return ret

    def unpack_color_list(self, binfile):
        return [binfile.read('4B', 4) for i in range(self.framecount)]

    def unpack(self, binfile):
        binfile.start()
        # data = binfile.read('256B', 0)
        # printCollectionHex(data)
        binfile.advance(4)  # ignore name
        [flags] = binfile.read('I', 4)  # flags: series of exists/isconstant
        enabled, is_constant = self.unpack_flags(flags)
        for i in range(len(enabled)):
            if enabled[i]:
                self.entry_masks.append(binfile.read('4B', 4))
                if is_constant[i]:
                    self.entries.append(binfile.read('4B', 4))
                else:
                    self.entries.append(binfile.bl_unpack(self.unpack_color_list, False))
        binfile.end()
        return self

    def pack(self, binfile):
        binfile.start()
        binfile.storeNameRef(self.name)
        binfile.write('I', self.pack_flags())
        enabled = self.flags
        is_constant = self.is_constant
        entries = self.entries
        masks = self.entry_masks
        color_lists = []
        entry_i = 0
        for i in range(len(enabled)):
            if enabled[i]:
                binfile.write('4B', *masks[entry_i])
                if is_constant[i]:
                    binfile.write('4B', *entries[entry_i])
                else:
                    binfile.mark()  # mark and come back
                    color_lists.append(entries[entry_i])
                entry_i += 1
        for x in color_lists:
            binfile.createRefFromStored()
            for i in range(self.framecount):
                binfile.write('4B', *x[i])
        binfile.end()


class Clr0(SubFile):
    """ Clr0 class """
    MAGIC = "CLR0"
    EXT = 'clr0'
    VERSION_SECTIONCOUNT = {4: 2, 3: 1}
    EXPECTED_VERSION = 4
    SETTINGS = ('framecount', 'loop')

    def __init__(self, name, parent, binfile=None):
        super(Clr0, self).__init__(name, parent, binfile)
        self.animations = []

    def begin(self, initial_values=None):
        self.loop = True
        self.framecount = 1

    def paste(self, item):
        self.animations = deepcopy(item.animations)
        self.loop = item.loop
        self.framecount = item.framecount

    def set_str(self, key, value):
        return set_anim_str(self, key, value)

    def get_str(self, key):
        return get_anim_str(self, key)

    def unpack(self, binfile):
        # data = binfile.read('256B', 0)
        # printCollectionHex(data)
        self._unpack(binfile)
        _, self.framecount, num_entries, self.loop = binfile.read('i2Hi', 12)
        binfile.recall()  # section 0
        folder = Folder(binfile)
        folder.unpack(binfile)
        while len(folder):
            anim = Clr0Animation(folder.recallEntryI(), self.framecount, self.loop)
            self.animations.append(anim.unpack(binfile))
        binfile.end()

    def pack(self, binfile):
        self._pack(binfile)
        animations = self.animations
        binfile.write('i2Hi', 0, self.framecount, len(animations), self.loop)
        binfile.createRef()  # section 0
        folder = Folder(binfile)
        for x in animations:
            folder.addEntry(x.name)
        folder.pack(binfile)
        for x in animations:
            folder.createEntryRefI()
            x.pack(binfile)
        binfile.end()

