from abmatt.brres.lib.packing.interface import Packer


def pack_default(subfile, binfile):
    p = PackSubfile(subfile, binfile)
    binfile.writeRemaining(subfile.data)
    # create the offsets
    for i in subfile.offsets:
        binfile.writeOffset("I", binfile.unmark(), i)
    binfile.end()


class PackSubfile(Packer):
    def pack(self, subfile, binfile):
        """ packs sub file into binfile, subclass must use binfile.end() """
        binfile.start()
        binfile.writeMagic(subfile.MAGIC)
        binfile.markLen()
        binfile.write("I", subfile.version)
        binfile.writeOuterOffset()
        # mark section offsets to be added later
        binfile.mark(subfile.get_num_sections())
        # name offset to be packed separately
        binfile.storeNameRef(subfile.name)
