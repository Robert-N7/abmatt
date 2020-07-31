"""Model Drawlist class"""
from brres.lib.binfile import UnpackingError


class Definition():
    """ Definition, controls drawing commands such as opacity"""
    names = ("DrawOpa", "DrawXlu", "MixNode", "NodeTree")

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.isMixed = False
        if 'Draw' in self.name:
            self.cmd = 0x4
        elif self.name == 'NodeTree':
            self.cmd = 0x2
        else:
            self.isMixed = True
        self.list = []

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


class DrawList():
    """List exclusively with drawing definitions such as opacity"""
    class DrawEntry():
        def __init__(self, binfile):  # unpacks immediately
            self.matIndex, self.objIndex, self.boneIndex, self.priority = binfile.read("3HB", 7)

        def pack(self, binfile):
            binfile.write("3HB", self.matIndex, self.objIndex, self.boneIndex, self.priority)

        def getPriority(self):
            return self.priority

        def setPriority(self, val):
            self.priority = val

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.list = []

    def __len__(self):
        return len(self.list)

    def __bool__(self):
        return len(self.list) > 0

    def pop(self, materialID):
        li = self.list
        for i in range(len(li)):
            if li[i].matIndex == materialID:
                return li.pop(i)

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
            assert(byte == 0x4)
            li.append(self.DrawEntry(binfile))

    def pack(self, binfile):
        for x in self.list:
            binfile.write("B", 0x4)
            x.pack(binfile)
        binfile.write("B", 0x1)