from abmatt.brres.lib.node import Node


def get_definition(name, parent, binfile=None):
    if name in ("DrawOpa", "DrawXlu"):
        d = DrawList(name, parent, binfile)
    elif name == 'NodeTree':
        d = NodeTree(name, parent, binfile)
    elif name == 'NodeMix':
        d = NodeMix(name, parent, binfile)
    else:
        raise ValueError(f'Definition {name} unknown')
    if binfile:
        d.unpack(binfile)
    return d


class NodeMix(Node):
    def __init__(self, name, parent, binfile=None):
        self.mixed_weights = []
        self.fixed_weights = []
        super().__init__(name, parent, binfile)

    def __bool__(self):
        return bool(self.mixed_weights)

    def add_mixed_weight(self, weight_id, weights):
        """
        :param weight_id:   the id that is referenced by facepoints
        :param weights:     list of 2-tuples [(bone_id, weight), ...]
        """
        weight = self.MixedWeight(weight_id)
        weight.weights = weights
        self.mixed_weights.append(weight)

    def add_fixed_weight(self, weight_id, bone_id):
        self.fixed_weights.append(self.FixedWeight(weight_id, bone_id))

    # def create_or_find_influence(self, influence):
    #     if len(influence) > 1:
    #         for x in self.mixed_weights:
    #             if x.inf_eq(influence):
    #                 return x.weight_id
    #         # wasn't found! Let's create it
    #         weight = self.MixedWeight(len(self.mixed_weights) + len(self.fixed_weights))
    #         for x in influence:
    #             weight.add_weight(*x)
    #         return weight.weight_id
    #     else:
    #         # search in fixed weights
    #         for x in self.fixed_weights:
    #             if x.bone_id == influence[0]:
    #                 return x.weight_id
    #         # wasn't found! Let's create it
    #         weight = self.FixedWeight(len(self.mixed_weights) + len(self.fixed_weights), influence[0])
    #         return weight.weight_id

    class MixedWeight:
        def __init__(self, weight_id=None, binfile=None):
            if binfile:
                self.__unpack(binfile)
            else:
                self.weight_id = weight_id
                self.weights = []

        def __iter__(self):
            return iter(self.weights)

        def __next__(self):
            return next(self.weights)

        # def inf_eq(self, influence):
        #     weights = self.weights
        #     if len(weights) != len(influence):
        #         return False
        #     for i in range(len(weights)):
        #         if weights[i] != influence[i]:
        #             return False
        #     return True
        #
        # def to_inf(self):
        #     return [x for x in self.weights]

        def add_weight(self, x):
            self.weights.append(x)

        def __unpack(self, binfile):
            self.weight_id, weight_count = binfile.read("HB", 3)
            self.weights = [binfile.read('Hf', 6) for i in range(weight_count)]

        def pack(self, binfile):
            binfile.write('HB', self.weight_id, len(self.weights))
            for x in self.weights:
                binfile.write('Hf', *x)

    class FixedWeight:
        def __init__(self, weight_id, bone_id):
            self.weight_id = weight_id
            self.bone_id = bone_id

        def to_inf(self):
            return [(self.bone_id, 1.0)]

    def unpack(self, binfile):
        while True:
            [cmd] = binfile.read('B', 1)
            if cmd == 3:
                self.mixed_weights.append(self.MixedWeight(binfile=binfile))
            elif cmd == 5:
                self.fixed_weights.append(self.FixedWeight(*binfile.read('2H', 4)))  # (weight_id, bone_id)
            elif cmd == 1:
                break
            else:
                raise ValueError(f'Unknown NodeMix cmd {cmd}')

    def pack(self, binfile):
        for x in self.fixed_weights:
            binfile.write('B2H', 5, x.weight_id, x.bone_id)
        for x in self.mixed_weights:
            binfile.write('B', 3)
            x.pack(binfile)
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
        def __init__(self, is_xlu, binfile=None):  # unpacks immediately
            self.xlu = is_xlu
            if binfile:
                self.matIndex, self.objIndex, self.boneIndex, self.priority = binfile.read("3HB", 7)

        def begin(self, mat_id, obj_id, bone_id, priority=0):
            self.matIndex = mat_id
            self.objIndex = obj_id
            self.boneIndex = bone_id
            self.priority = priority
            return self

        def is_xlu(self):
            return self.xlu

        def pack(self, binfile):
            binfile.write("3HB", self.matIndex, self.objIndex, self.boneIndex, self.priority)

        def getPriority(self):
            return self.priority

        def setPriority(self, val):
            self.priority = val

    def __init__(self, name, parent, binfile=None):
        self.list = []
        self.is_xlu = ('Xlu' in name)
        super().__init__(name, parent, binfile)

    def __len__(self):
        return len(self.list)

    def __bool__(self):
        return len(self.list) > 0

    def pop(self, draw_entry):
        li = self.list
        for i in range(len(li)):
            if li[i] is draw_entry:
                return li.pop(i)

    def add_entry(self, material_id, polygon_id, bone_id=0, priority=0):
        self.list.append(self.DrawEntry(self.is_xlu).begin(material_id, polygon_id, bone_id, priority))

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

    def sort(self):
        self.list = sorted(self.list, key=lambda x: (x.priority, x.matIndex))

    def unpack(self, binfile):
        li = self.list
        while True:
            [byte] = binfile.read("B", 1)
            if byte == 0x1:
                break
            assert (byte == 0x4)
            li.append(self.DrawEntry(self.is_xlu, binfile))

    def pack(self, binfile):
        for x in self.list:
            binfile.write("B", 0x4)
            x.pack(binfile)
        binfile.write("B", 0x1)
