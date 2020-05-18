#--------------------------------------------------------
#   Brres Class
#--------------------------------------------------------
from model import *
from material import *
from layer import *
from shader import *
from struct import *
from pack import *
from fileobject import *

class Brres:
    structs = {
        "h" : Struct("> 4s H H I H H"),
        "root" : Struct("> 4s I"),
        "indexGroupH" : Struct("> I I"),
        "indexGroup" : Struct("> H H H H I I"),
    }

    def __init__(self, filename):
        self.filename = filename
        self.models = []
        self.textures = []
        self.anmClr = []
        self.anmTexSrt = []
        self.isModified = False
        self.isUpdated = False
        self.file = Bin(self.filename, self)
        try:
            self.unpack(self.file)
        except ValueError as e:
            print("Error parsing '{}': {}".format(fname, e))
            sys.exit(1)
            return

    def unpack(self, file):
        brresHd = file.read(self.structs["h"], 16)
        if brresHd[0] != "bres":
            return False
        file.offset = brresHd[4]
        self.brresHd = brresHd
        self.rootHd = file.read(self.structs["root"], 8)
        self.indexGroups = []
        self.subFiles = []
        self.root = IndexGroup(f, 0)
        for offset in self.root.entryOffsets:
            self.indexGroups.append(IndexGroup(f, offset))
        for group in self.indexGroups:
            # folderNames = group.entryNames
            offsets = group.entryOffsets
            names = group.entryNames
            for i in range(len(offsets)):
                # print("\t=====Folder {}======".format(folderNames[i]))
                self.subFiles.append(BresSubFile(f, offsets[i], names[i]))
        return True

    def pack(self, brres):
        pass

    def getModelsByName(self, name):
        return findAll(name, self.models)

    def save(self, filename, overwrite):
        if not filename:
            filename = self.filename
            if not self.isChanged():
                return
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            PackBrres(self)
            packed = self.file
            # packed.convertByteArr()
            f = open(filename, "wb")
            f.write(packed.file)
            f.close()
            print("Wrote file '{}'".format(filename))
            return True

    def setModel(self, modelname):
        for mdl in self.models:
            if modelname == mdl.name:
                self.model = mdl
                return True
        regex = re.compile(modelname)
        if regex:
            for mdl in self.models:
                if regex.search(modelname):
                    self.model = mdl
                    return True
        return False

    def parseCommand(self, command):
        if command.cmd == command.COMMANDS[0]:
            self.set(command)
        elif command.cmd == command.COMMANDS[1]:
            self.info(command, "")
        else:
            print("Unknown command: {}".format(self.cmd))

    def info(self, command, trace):
        # todo trace?
        if command.modelname:  # narrow scope and pass
            models = findAll(command.modelname, self.models)
            if models:
                for x in models:
                    x.info(command, trace)
        else:
            for x in self.models:
                x.info(command, trace)

    def set(self, command):
        mats = self.getMatCollection(command.modelname, command.materialname)
        if command.key in Layer.SETTINGS:
            layers = self.getLayerCollection(mats, command.name)
            if layers:
                self.layersSet(layers, command.key, command.value)
            else:
                print("No matches found for {}".format(command.name))
        else:
            mats = findAll(command.name, mats)
            if mats:
                self.materialSet(mats, command.key, command.value)
            else:
                print("No matches found for {}".format(command.name))


    def getModelByOffset(self, offset):
        for mdl in self.models:
            if offset == mdl.offset:
                return mdl


    def getMatCollection(self, modelname, materialname):
        mdls = findAll(modelname, self.models)
        mats = []
        for mdl in mdls:
            found = findAll(materialname, mdl.mats)
            if found:
                mats = mats + found
        return mats

    def getLayerCollection(self, mats, layername):
        layers = []
        for m in mats:
            found =  findAll(layername, m.layers)
            if found:
                layers = layers + found
        return layers

    def materialSet(self, materials, setting, value):
        try:
            func = materials[0].getSetter(setting)
            if func:
                for x in materials:
                    func(x, value)
            else:
                print("Unknown setting {}".format(setting))
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        self.isUpdated = True
        return True

    def layersSet(self, layers, setting, value):
        try:
            fun = layers[0].getSetter(setting)
            if not fun:
                print("Unknown setting {}".format(setting))
                return False
            else: # FUN!
                for x in layers:
                    fun(x, value)
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        self.isUpdated = True
        return True

    def isChanged(self):
        if self.isModified:
            return True
        if self.isUpdated:
            for mdl in self.models:
                if mdl.isChanged():
                    self.isModified = True # to prevent checking further
                    return True
        self.isUpdated = False
        return False

class IndexGroup:
    structs = {
        "h" : Struct("> I I"),
        "indexGroup" : Struct("> H H H H I I"),
    }
    def __init__(self, file, offset):
        if offset:
            file.offset = offset
        self.isModified = False
        self.offset = file.offset
        self.h = file.read(self.structs["h"], 8)
        # print("Group byte len, numEntries: {}".format(self.h))
        self.entries = []
        self.entryNames = []
        self.entryOffsets = []
        # file.offset += 16
        for i in range(self.h[1] + 1):
            entry = file.read(self.structs["indexGroup"], 16)
            # if self.h[1] == 3:
            # print("{} Entry id, uk, left, right, namep, datap {}".format(file.offset - 16, entry))
            if i != 0:
                name = file.unpack_name(entry[4] + self.offset)
                self.entryNames.append(name)
                self.entryOffsets.append(entry[5] + self.offset)
            # else:
            #     self.entryNames.append("Null")

            self.entries.append(entry)

    def updateEntryOffset(self, offset, index):
        self.entryOffsets[index] = offset
        self.isModified = True

    # does not handle changing left right id etc
    def repack(self, file):
        if not self.isModified:
            return
        offset = self.offset
        # pack header
        pack_into("> I I", file.file, offset, self.h[0], self.h[1])
        offset += 8
        # pack entries
        for i in range(len(self.entries)):
            entry = self.entries[i]
            entryOffset = entry[5] if i == 0 else self.entryOffsets[i - 1] - self.offset
            # print("Offset is {} for entry {}".format(self.offset + entryOffset, self.entries[i]))
            pack_into("> 4H 2I", file.file, offset, entry[0], entry[1], entry[2],
            entry[3], entry[4], entryOffset)
            offset += 16
