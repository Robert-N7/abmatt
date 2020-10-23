from abmatt.brres.lib.binfile import UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker


def unpack_default(subfile, binfile):
    UnpackSubfile(subfile, binfile)
    subfile.data = binfile.readRemaining()
    offsets = []
    for i in range(subfile._getNumSections()):
        offsets.append(binfile.recall())
    subfile.offsets = offsets
    binfile.end()


class UnpackSubfile(Unpacker):
    def unpack(self, subfile, binfile):
        """ unpacks the sub file, subclass must use binfile.end() """
        offset = binfile.start()
        magic = binfile.readMagic()
        if magic != subfile.MAGIC:
            raise UnpackingError(binfile, 'Magic {} does not match expected {}'.format(magic, subfile.MAGIC))
        binfile.readLen()
        subfile.version, outerOffset = binfile.read("Ii", 8)
        try:
            subfile.numSections = subfile._getNumSections()
        except ValueError:
            raise UnpackingError(binfile,
                                 "{} {} unsupported version {}".format(subfile.MAGIC, subfile.name, subfile.version))
        binfile.store(subfile.numSections)  # store section offsets
        subfile.name = binfile.unpack_name()
