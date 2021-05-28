from abmatt.kmp.checkpoint import CheckPointGroup
from abmatt.kmp.cpu_route import CpuRoute
from abmatt.kmp.item_route import ItemRoute
from abmatt.lib.binfile import PackingError
from abmatt.lib.pack_interface import Packer


class PackSection(Packer):
    klass = None

    def __init__(self, node, binfile, added_value=0):
        self.added_value = added_value
        super().__init__(node, binfile)

    def pack_data(self, node, binfile):
        raise NotImplementedError()

    def pack(self, nodes, binfile):
        binfile.write_magic(self.klass.MAGIC)
        binfile.write('2H', len(nodes), self.added_value)
        for n in nodes:
            self.pack_data(n, binfile)


class PackHeader(PackSection):
    @staticmethod
    def __get_links(items, binfile):
        indices = [x.index for x in items]
        if len(indices) < 6:
            indices.extend([0xff] * (6 - len(indices)))
        elif len(indices) > 6:
            raise PackingError(binfile, '{} linked to {} groups, {} max'.format(items[0].MAGIC, len(indices), 6))
        return indices

    def pack_data(self, node, binfile):
        start = node[0].index if len(node) else 0xff
        binfile.write(self.klass.FMT, start, len(node),
                      *self.__get_links(node.prev_groups, binfile),
                      *self.__get_links(node.next_groups, binfile),
                      *node.settings)


class PackCkph(PackHeader):
    klass = CheckPointGroup


class PackItph(PackHeader):
    klass = ItemRoute


class PackEnph(PackHeader):
    klass = CpuRoute