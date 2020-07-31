from brres.lib.autofix import Bug
from brres.mdl0.geometry import Geometry


class Vertex(Geometry):
    """ Vertex class for storing vertices data """

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
        return self

    def pack(self, binfile):
        """ Packs into binfile """
        super(Vertex, self).pack(binfile)
        binfile.write('3f', *self.minimum)
        binfile.write('3f', *self.maximum)
        binfile.advance(8)
        binfile.createRef()  # data pointer
        binfile.writeRemaining(self.data)
        binfile.end()
