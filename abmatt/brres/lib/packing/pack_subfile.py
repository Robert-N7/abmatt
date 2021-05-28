from abmatt.lib.pack_interface import Packer


def pack_default(subfile, binfile):
    p = PackSubfile(subfile, binfile)
    binfile.write_remaining(subfile.data)
    # create the offsets
    for i in subfile.offsets:
        binfile.write_offset("I", binfile.unmark(), i)
    binfile.end()


class PackSubfile(Packer):
    def pack(self, subfile, binfile):
        """ packs sub file into binfile, subclass must use binfile.end() """
        binfile.start()
        binfile.write_magic(subfile.MAGIC)
        binfile.mark_len()
        binfile.write("I", subfile.version)
        binfile.write_outer_offset()
        # mark section offsets to be added later
        binfile.mark(subfile._getNumSections())
        # name offset to be packed separately
        binfile.store_name_ref(subfile.name)
