from brres.lib.autofix import Bug
from brres.mdl0.geometry import Geometry


class Vertex(Geometry):
    """ Vertex class for storing vertices data """

    def encode_data(self, point_collection):
        comp_count = super(Vertex, self).encode_data(point_collection)
        if comp_count == 2:
            self.comp_count = 0  # xy position
        elif comp_count == 3:
            self.comp_count = 1  # xyz
        else:
            raise ValueError('Component count {} for vertex {} out of range.'.format(comp_count, self.name))

    def __str__(self):
        return 'Vertex {} id:{} xyz:{} format:{} divisor:{} stride:{} count:{}'.format(self.name, self.index,
                                                                                       self.comp_count,
                                                                                       self.format, self.divisor,
                                                                                       self.stride, self.count)

    def unpack(self, binfile):
        """ Unpacks some ptrs but mostly just leaves data as bytes """
        super(Vertex, self).unpack(binfile)
        self.minimum = binfile.read('3f', 12)
        self.maximum = binfile.read('3f', 12)
        binfile.recall()
        self.data = binfile.readRemaining()
        binfile.end()

    def pack(self, binfile):
        """ Packs into binfile """
        super(Vertex, self).pack(binfile)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        binfile.advance(8)
        binfile.createRef()  # data pointer
        binfile.writeRemaining(self.data)
        binfile.alignAndEnd()
