

class Packer:
    def __init__(self, node, binfile):
        self.node = node
        self.binfile = binfile
        self.pack(node, binfile)

    def pack(self, node, binfile):
        raise NotImplementedError()