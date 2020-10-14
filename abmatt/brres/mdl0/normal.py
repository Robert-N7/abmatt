from abmatt.brres.mdl0.point import Point


class Normal(Point):

    def pack(self, binfile):
        super(Normal, self).pack(binfile)
        self.pack_data(binfile)
