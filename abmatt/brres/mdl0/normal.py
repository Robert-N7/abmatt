from brres.mdl0.geometry import Geometry


class Normal(Geometry):
    def encode_data(self, point_collection):
        comp_count = super(Normal, self).encode_data(point_collection)
        # comp count has to be set manually if it's 0x2 (normal or binormal or tangent) since it's also 3 width
        if comp_count == 3:
            self.comp_count = 0
        elif comp_count == 9:
            self.comp_count = 1
        else:
            raise ValueError('Component count {} for normal {} out of range'.format(comp_count, self.name))

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
        binfile.alignAndEnd()
