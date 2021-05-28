
class Unpacker:
    def __init__(self, node, binfile):
        self.node = node
        self.binfile = binfile
        self.unpack(node, binfile)

    def unpack(self, node, binfile):
        raise NotImplementedError()