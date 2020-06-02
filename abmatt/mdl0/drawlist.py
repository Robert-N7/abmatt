"""Model Drawlist class"""


class Definition():
    ''' Definition, controls drawing commands such as opacity'''
    names = ("DrawOpa", "DrawXlu", "MixNode", "NodeTree")  # todo check these

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
                    weight_id, weight_count, table_id = binfile.read("3H", 6)
                    weights = 4 * weight_count
                    weights = binfile.read("{}B".format(weights), weights)  # not sure if these are ints
                    drawl = [weight_id, weight_count, table_id] + list(weights)
                    current_list.append(drawl)
                elif byte > 0x6:  # error reading list?
                    print("Error unpacking list {}".format(current_list))
                    break
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

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.list = []

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