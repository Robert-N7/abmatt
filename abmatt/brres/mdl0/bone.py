from brres.lib.node import Node


class Bone(Node):
    """ Bone class """
    def unpack(self, binfile):
        self.offset = binfile.start()
        binfile.readLen()
        binfile.advance(8)
        self.index, self.bone_id, self.flags, self.billboard = binfile.read('4I', 20)
        self.scale = binfile.read('3f', 12)
        self.rotation = binfile.read('3f', 12)
        self.translation = binfile.read('3f', 12)
        self.minimum = binfile.read('3f', 12)
        self.maximum = binfile.read('3f', 12)
        self.b_parent, self.child, self.sibling, self.prev, self.part2 = binfile.read('5I', 20)
        self.transform_matrix = binfile.read('12f', 48)
        self.inverse_matrix = binfile.read('12f', 48)
        binfile.end()

    def pack(self, binfile):
        self.offset = binfile.start()
        binfile.markLen()
        binfile.write('i', binfile.getOuterOffset())
        binfile.storeNameRef(self.name)
        binfile.write('5I', self.index, self.bone_id, self.flags, self.billboard, 0)
        binfile.write('3f', *self.scale)
        binfile.write('3f', *self.rotation)
        binfile.write('3f', *self.translation)
        binfile.write('I', self.b_parent.offset - self.offset)
        # todo

        binfile.end()



    def pack(self, binfile):
        pass

class BoneTable:
    """ Bonetable class """

    def unpack(self, binfile):
        """ unpacks bonetable """
        [length] = binfile.read("I", 4)
        self.entries = binfile.read("{}I".format(length), length * 4)

    def pack(self, binfile):
        length = len(self.entries)
        binfile.write("I", length)
        binfile.write("{}I".format(length), *self.entries)
