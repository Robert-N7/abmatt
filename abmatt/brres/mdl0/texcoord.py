from abmatt.brres.mdl0.point import Point


class TexCoord(Point):
    @property
    def DEFAULT_WIDTH(self):
        return 2

    def begin(self):
        super(TexCoord, self).begin()

    def pack(self, binfile):
        super(TexCoord, self).pack(binfile)
        binfile.write('2f', *self.minimum)
        binfile.write('2f', *self.maximum)
        self.pack_data(binfile)
