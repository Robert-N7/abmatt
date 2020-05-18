#!/usr/bin/python
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
import sys
import os
import binascii

class BresSubFile:
    structs = {
        "h" : Struct("> 4s I I I")
    }
    numSections = {
        "CHR03" : 1,
        "CHR05" : 5,
        "CLR04" : 2,
        "MDL08" : 11,
        "MDL011" : 14,
        "PAT04" : 6,
        "SCN04" : 6,
        "SCN05" : 7,
        "SHP04" : 3,
        "SRT04" : 1,
        "SRT05" : 2,
        "TEX01" : 1,
        "TEX02" : 2,
        "TEX03" : 1
    }
    def __init__(self, file, offset, name):
        self.offset = file.offset = offset
        self.name = name
        self.h = file.read(self.structs["h"], 16)
        # print("Subfile, len, version, outerOffset: {}".format(self.h))
        self.magic = self.h[0]
        self.length = self.h[1]
        self.version = self.h[2]
        # self.bin = file.file[self.offset:self.offset + self.length]
        self.sectionCount = self.numSections[self.magic.decode() + str(self.version)]
        # print("section count: {}".format(self.sectionCount))
        self.sectionOffsets = file.read(Struct("> " + str(self.sectionCount) + "I" ), self.sectionCount * 4)
        # print("{} Section offsets: {}".format(self.magic, self.sectionOffsets))
        if self.magic == b"MDL0":
            Model(file, self)


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
            if not self.unpack(self.file):
                print("Error parsing '{}'".format(filename))
                sys.exit(1)
        except ValueError as e:
            print("Error parsing '{}': {}".format(filename, e))
            sys.exit(1)

    def unpack(self, file):
        brresHd = file.read(self.structs["h"], 16)
        if brresHd[0].decode() != "bres":
            print("Not a brres file {}".format(brresHd[0]))
            return False
        file.offset = brresHd[4]
        self.brresHd = brresHd
        self.rootHd = file.read(self.structs["root"], 8)
        self.indexGroups = []
        self.subFiles = []
        self.root = IndexGroup(file, 0)
        for offset in self.root.entryOffsets:
            self.indexGroups.append(IndexGroup(file, offset))
        for group in self.indexGroups:
            # folderNames = group.entryNames
            offsets = group.entryOffsets
            names = group.entryNames
            for i in range(len(offsets)):
                # print("\t=====Folder {}======".format(folderNames[i]))
                self.subFiles.append(BresSubFile(file, offsets[i], names[i]))
        return self.models

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
