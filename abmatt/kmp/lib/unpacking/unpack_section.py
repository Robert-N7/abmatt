from abmatt.lib.binfile import UnpackingError
from abmatt.lib.unpack_interface import Unpacker


class UnpackSection(Unpacker):
    klass = None

    def post_unpack(self, args):
        pass

    def resolve(self, items, index):
        return items[index] if 0 <= index < len(items) else None

    def unpack_data(self, binfile):
        return binfile.read(self.klass.FMT, self.klass.BYTE_LEN)

    def unpack(self, node, binfile):
        magic = binfile.read_magic()
        if magic != self.klass.MAGIC:
            raise UnpackingError(binfile, 'Wrong section magic {}'.format(magic))
        self.n_entries, self.additional_val = binfile.read('2H', 4)
        self.nodes = [self.unpack_data(binfile) for i in range(self.n_entries)]


class UnpackHead(UnpackSection):
    def post_unpack(self, args):
        routes = [self.klass(args[x[0]: x[0] + x[1]], list(x[14:])) for x in
                  self.nodes]
        for j in range(len(routes)):
            x = self.nodes[j]
            routes[j].prev_groups = \
                [routes[x[i]] for i in range(2, 8) if 0 <= x[i] < len(routes)]
            routes[j].next_groups = \
                [routes[x[i]] for i in range(8, 14) if 0 <= x[i] < len(routes)]
        return routes

    def unpack_data(self, binfile):
        return binfile.read(self.klass.FMT, 16)
