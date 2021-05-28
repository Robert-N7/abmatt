from abmatt.lib.pack_interface import Packer


class UnknownPacker(Packer):
    def pack(self, node, binfile):
        binfile.write('{}B'.format(len(node.data)), *node.data)
