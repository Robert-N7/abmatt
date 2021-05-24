from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.packing.interface import Packer


class UnknownPacker(Packer):
    def pack(self, node, binfile):
        binfile.write('{}B'.format(len(node.data)), *node.data)
