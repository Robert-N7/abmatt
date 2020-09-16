from abmatt.brres.lib.binfile import UnpackingError, printCollectionHex
from abmatt.brres.lib.node import Node


class Definition(Node):
    """ Definition, controls drawing commands and Node commands etc"""
    names = ("DrawOpa", "DrawXlu", "MixNode", "NodeTree")

    def __init__(self, name, parent, binfile=None):
        self.isMixed = True     # assumes mixed
        self.list = []
        super().__init__(name, parent, binfile)

    def unpack(self, binfile):
        """ unpacks draw list """
        current_list = self.list
        while True:
            [byte] = binfile.read("B", 1)
            if byte == 0x01:  # end list
                break
            else:
                current_list.append(byte)
                if byte == 0x4:
                    current_list.append(binfile.read("7B", 7))
                elif byte == 0x3:
                    weight_id, weight_count = binfile.read("HB", 3)
                    weights = [binfile.read('Hf', 6) for i in range(weight_count)]  # index, weight
                    drawl = [weight_id, weight_count] + weights
                    current_list.append(drawl)
                elif byte > 0x6:  # error reading list?
                    raise UnpackingError(binfile, "Error unpacking definitions")
                else:
                    current_list.append(binfile.read("4B", 4))

    def pack(self, binfile):
        """ packs the definition"""
        cmd = True
        for x in self.list:
            if cmd:
                binfile.write("B", x)
            else:
                binfile.write("{}B".format(len(x)), *x)
            cmd = not cmd
        binfile.write("B", 0x01)  # end list command


class NodeTree(Node):

    def __init__(self, name, parent, binfile=None):
        self.nodes = []
        super().__init__(name, parent, binfile)

    def add_entry(self, bone_index, parent_index):
        self.nodes.append((bone_index, parent_index))

    def unpack(self, binfile):
        nodes = self.nodes
        while True:
            [byte] = binfile.read('B', 1)
            if byte == 0x1:
                break
            assert byte == 0x2
            nodes.append(binfile.read('2H', 4))

    def pack(self, binfile):
        for x in self.nodes:
            binfile.write('B2H', 0x2, x[0], x[1])
        binfile.write('B', 0x1)  # end


class DrawList(Node):
    """List exclusively with drawing definitions such as opacity"""

    class DrawEntry:
        def __init__(self, binfile=None):  # unpacks immediately
            if binfile:
                self.matIndex, self.objIndex, self.boneIndex, self.priority = binfile.read("3HB", 7)

        def begin(self, mat_id, obj_id, bone_id, priority=0):
            self.matIndex = mat_id
            self.objIndex = obj_id
            self.boneIndex = bone_id
            self.priority = priority
            return self

        def pack(self, binfile):
            binfile.write("3HB", self.matIndex, self.objIndex, self.boneIndex, self.priority)

        def getPriority(self):
            return self.priority

        def setPriority(self, val):
            self.priority = val

    def __init__(self, name, parent, binfile=None):
        self.list = []
        super().__init__(name, parent, binfile)

    def __len__(self):
        return len(self.list)

    def __bool__(self):
        return len(self.list) > 0

    def pop(self, materialID):
        li = self.list
        for i in range(len(li)):
            if li[i].matIndex == materialID:
                return li.pop(i)

    def add_entry(self, material_id, polygon_id, bone_id=0, priority=0):
        self.list.append(self.DrawEntry().begin(material_id, polygon_id, bone_id, priority))

    def insert(self, drawEntry):
        priority = drawEntry.priority
        li = self.list
        for i in range(len(li)):
            if priority <= li[i].priority:
                li.insert(i, drawEntry)
                return
        li.append(drawEntry)

    def getByMaterialID(self, id):
        for x in self.list:
            if x.matIndex == id:
                return x

    def getByObjectID(self, id):
        for x in self.list:
            if x.objIndex == id:
                return x

    def setPriority(self, id, priority):
        definition = self.getByMaterialID(id)
        if not definition:
            return False
        definition.setPriority(priority)
        self.list.sort(key=lambda x: x.priority)
        return True

    def unpack(self, binfile):
        li = self.list
        while True:
            [byte] = binfile.read("B", 1)
            if byte == 0x1:
                break
            assert (byte == 0x4)
            li.append(self.DrawEntry(binfile))

    def pack(self, binfile):
        for x in self.list:
            binfile.write("B", 0x4)
            x.pack(binfile)
        binfile.write("B", 0x1)
