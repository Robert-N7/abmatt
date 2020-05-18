# -------------------------------------------------------------
#   File Oject class
# -------------------------------------------------------------
from struct import *

class FileObject:
    def __init__(self, file, parent):
        self.file = file
        self.name = ""
        self.length = 0
        self.parent = parent
        self.children = []
        self.isModified = False
        self.offsetChanged = False
        if self.parent:
            self.parent.children.append(self)
        self.unpack()

# To be implemented in underlying
    # def pack(self):
    #     pass
    #
    # def unpack(self):
    #     pass
    def setOffset(self, offset):
        if offset != self.offset:
            self.offset = offset
            self.offsetChanged = True
            self.isModified = True

    def setLength(self, len):
        if len != self.length:
            self.length = len
            self.isModified = True


    def info(self, command, trace):
        trace += "->" + self.name
        for item in self.children:
            item.info(command, trace)

# --------------------------------------------------------
# Subfile
# --------------------------------------------------------
class SubFile(FileObject):
    HEADER = ">4s2Ii"
    def __init__(self, file, parent):
        super().__init__(file, parent)


    def unpack(self):
        header = file.read(self.HEADER, 16)
        self.magic = header[0]
        self.length = header[1]
        self.version = header[2]
        self.outerOffset = header[3]

    def pack(self):
        self.file.offset = self.offset
        self.file.write(self.HEADER, 16, self.magic, self.length, self.version, self.outerOffset)

    def setOuterOffset(self, offset):
        self.outerOffset = offset - self.offset

# Class for reading from binary file
class Bin:
    def __init__(self, filename, container):
        self.container = container
        self.offset = 0
        file = open(filename, "rb")
        self.file = file.read()
        file.close()

    def read(self, struct, len):
        packed = self.file[self.offset:(self.offset + len)]
        self.offset += len
        return struct.unpack(packed)

    def write(self, struct, len, args):
        pack_into(struct, self.file, self.offset, len, args)
        self.offset += len

    def readOffset(self, struct, offset, len):
        packed = self.file[offset:(offset + len)]
        return struct.unpack(packed)

    def writeOffset(self, struct, offset, len, args):
        pack_into(struct, self.file, offset, len, args)

    def unpack_name(self, offset):
        nameLens = self.readOffset(Struct("> I"), offset - 4, 4)
        if nameLens[0] > 256:
            print("Name length too long!")
        else:
            name = self.readOffset(Struct("> " + str(nameLens[0]) + "s"), offset, nameLens[0]);
            # print("Name: {}".format(name[0]))
            return name[0]

    def convertByteArr(self):
        if type(self.file) != bytearray:
            self.file = bytearray(self.file)
