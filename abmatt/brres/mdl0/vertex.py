from abmatt.brres.mdl0.geometry import Geometry


class Vertex(Geometry):
    """ Vertex class for storing vertices data """
    COMP_COUNT = (2, 3)
    def __str__(self):
        return 'Vertex {} id:{} xyz:{} format:{} divisor:{} stride:{} count:{}'.format(self.name, self.index,
                                                                                       self.comp_count,
                                                                                       self.format, self.divisor,
                                                                                       self.stride, self.count)

    def unpack(self, binfile):
        super(Vertex, self).unpack(binfile)
        self.minimum = binfile.read('3f', 12)
        self.maximum = binfile.read('3f', 12)
        self.unpack_data(binfile)

    def pack(self, binfile):
        """ Packs into binfile """
        super(Vertex, self).pack(binfile)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        self.pack_data(binfile)
