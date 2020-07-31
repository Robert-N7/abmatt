from brres.mdl0.geometry import Geometry


class Normal(Geometry):
    def unpack(self, binfile):
        super(Normal, self).unpack(binfile)
        binfile.recall()
        self.data = binfile.readRemaining()
        binfile.end()

    def pack(self, binfile):
        super(Normal, self).pack(binfile)
        binfile.align()
        binfile.createRef()
        binfile.writeRemaining(self.data)
        binfile.end()
