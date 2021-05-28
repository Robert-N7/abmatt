import struct

from abmatt.lib.binfile import Folder, UnpackingError
from abmatt.lib.unpack_interface import Unpacker


class UnknownFile:
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def __eq__(self, other):
        return other is not None and type(other) == UnknownFile and self.name == other.name and self.data == other.data


class UnknownFolder:
    def __init__(self, name, subfiles):
        self.name = name
        self.subfiles = subfiles

    def __eq__(self, other):
        return other is not None and type(other) == UnknownFolder and self.name == other.name \
               and self.subfiles == other.subfiles

class UnknownUnpacker(Unpacker):
    def __init__(self, binfile, boundary_offsets, node=None):
        self.is_folder = self.check_for_folder(binfile)
        self.boundary_offsets = boundary_offsets
        self.end_offset = self.get_next_offset(binfile, boundary_offsets)
        self.length = self.end_offset - binfile.offset
        super().__init__(node, binfile)

    def check_for_folder(self, binfile):
        """Detect if its a folder by reading the first entry"""
        try:
            id, u, left, right, name, dataptr = binfile.read_offset('4H2I', binfile.offset + 8)
            return id == 0xffff and u == 0 and name == 0 and dataptr == 0
        except struct.error:
            return False

    def get_next_offset(self, binfile, boundary_offsets):
        current_offset = binfile.offset
        next_offset = float('inf')
        for x in boundary_offsets:
            if current_offset < x < next_offset:
                next_offset = x
        if next_offset == float('inf'):
            raise UnpackingError(binfile, 'Failed to detect end offset after {}'.format(current_offset))
        if not self.is_folder:
            for i in range(current_offset, len(binfile.file)):
                if binfile.file[i] == 0:
                    i += 1
                    if next_offset < i:
                        return next_offset
                    return i
        return next_offset

    def unpack(self, node, binfile):
        """Returns tuple(name, data, is_folder)"""
        if self.is_folder:
            folder = Folder(binfile, node)
            folder.unpack(binfile)
            entries = []
            for i in range(len(folder)):
                entries.append((folder.recall_entry_i(), binfile.offset))
                self.boundary_offsets.append(binfile.offset)
            entries = sorted(entries, key=lambda x: x[1])
            nodes = []
            for i in range(len(entries)):
                x = entries[i]
                binfile.offset = x[1]
                nodes.append(UnknownUnpacker(binfile, self.boundary_offsets, x[0]).node)
            self.node = UnknownFolder(node, nodes)
        else:
            self.node = UnknownFile(node, binfile.read('{}B'.format(self.length), 0))
