from abmatt.brres.mdl0.point import Point


class Vertex(Point):
    """ Vertex class for storing vertices data """
    def __str__(self):
        return 'Vertex {} id:{} xyz:{} format:{} divisor:{} stride:{} count:{}'.format(self.name, self.index,
                                                                                       self.comp_count,
                                                                                       self.format, self.divisor,
                                                                                       self.stride, self.count)

    def pack(self, binfile):
        """ Packs into binfile """
        super(Vertex, self).pack(binfile)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        self.pack_data(binfile)
