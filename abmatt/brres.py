#!/usr/bin/python
# --------------------------------------------------------
#   Brres Class
# --------------------------------------------------------
import os
import re
import string
import sys

from binfile import BinFile, Folder
from matching import findAll
from mdl0.layer import Layer
from mdl0.mdl0 import Mdl0
from srt0.srt0 import Srt0
from subfile import *


class Brres():
    FOLDERS = ["3DModels(NW4R)", "Textures(NW4R)", "AnmTexPat(NW4R)", "AnmTexSrt(NW4R)", "AnmChr(NW4R)",
               "AnmScn(NW4R)", "AnmShp(NW4R)", "AnmClr(NW4R)"]
    CLASSES = [Mdl0, Tex0, Pat0, Srt0, Chr0, Scn0, Shp0, Clr0]
    MAGIC = "bres"
    ROOTMAGIC = "root"
    OVERWRITE = False
    DESTINATION = None

    def __init__(self, name, parent=None, readFile=True):
        '''
            initialize brres
            name - the brres name, or filename
            parent - optional for supporting containing files in future
            readfile - optional start reading and unpacking file
        '''
        self.models = []
        self.textures = []
        self.anmSrt = []
        self.anmChr = []
        self.anmPat = []
        self.anmClr = []
        self.anmShp = []
        self.anmScn = []
        self.folders = [self.models, self.textures, self.anmPat, self.anmSrt, self.anmChr,
                        self.anmClr, self.anmShp, self.anmScn]
        self.isModified = False
        self.isUpdated = False
        self.parent = parent
        self.name = name
        if readFile:
            self.unpack(BinFile(self.name))

    def getModelsByName(self, name):
        return findAll(name, self.models)

    def close(self):
        self.save(self.DESTINATION, self.OVERWRITE)

    def save(self, filename, overwrite):
        if not filename:
            filename = self.name
            if not self.isChanged():
                return
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            f = BinFile(filename, mode="w")
            self.pack(f)
            f.commitWrite()
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
            print("Unknown command: {}".format(command.cmd))

    def getTrace(self):
        if self.parent:
            return self.parent.name + "->" + self.name
        return self.name

    def info(self, key=None, indentation_level=0):
        print('{}{}:\t{} models\t{} textures'.format('  ' * indentation_level, self.name,
                                                     len(self.models), len(self.textures)))
        indentation_level += 1
        for x in self.models:
            x.info(key, indentation_level)

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
            found = findAll(layername, m.layers)
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
            else:  # FUN!
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
                    self.isModified = True  # to prevent checking further
                    return True
        self.isUpdated = False
        return False

    def getNumSections(self, folders):
        """ gets the number of sections, including root"""
        count = 1   # root
        for x in folders[count:]:
            if x:
                count += len(x)
                # print('Length of folder {} is {}'.format(x.name, len(x)))
        return count

    def getTexture(self, name):
        for x in self.textures:
            if x.name == name:
                return x
        return None

    # ----------------- HOOKING REFERENCES ----------------------------------
    def hookAnimationRefs(self):
        """Hooks up references from materials to animations"""
        for x in self.anmSrt:
            name = x.name.rstrip(string.digits)
            for mdl in self.models:
                if name == mdl.name:
                    mdl.hookSRT0ToMats(x)

    # -------------------------------------------------------------------------
    #   PACKING / UNPACKING
    # -------------------------------------------------------------------------

    def unpackFolder(self, binfile, root, folderIndex):
        ''' Unpacks the folder folderIndex '''
        name = self.FOLDERS[folderIndex]
        if root.open(name):

            container = self.folders[folderIndex]
            subFolder = Folder(binfile, name)
            subFolder.unpack(binfile)
            klass = self.CLASSES[folderIndex]
            while True:
                nm = subFolder.openI()
                if not nm:
                    break
                obj = klass(nm, self)
                container.append(obj)
                obj.unpack(binfile)

    def unpack(self, binfile):
        """ Unpacks the brres """
        binfile.start()
        magic = binfile.readMagic()
        if magic != self.MAGIC:
            raise ValueError("Magic {} does not match {}".format(magic, self.MAGIC))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        pad, self.length, rootoffset, numSections = binfile.read("hI2h", 10)
        binfile.offset = rootoffset
        root = binfile.readMagic()
        assert (root == self.ROOTMAGIC)
        section_length = binfile.read("I", 4)
        root = Folder(binfile, root)
        root.unpack(binfile)
        # open all the folders
        for i in range(len(self.FOLDERS)):
            self.unpackFolder(binfile, root, i)
        binfile.end()
        self.hookAnimationRefs()

    def generateRoot(self, binfile):
        """ Generates the root folders
            Does not hook up data pointers except the head group,
            returns (rootFolders, bytesize)
        """
        rootFolders = []  # for storing Index Groups
        byteSize = 0
        # Create folder indexing folders
        rootFolder = Folder(binfile, self.ROOTMAGIC)
        rootFolders.append(rootFolder)
        offsets = []  # for tracking offsets from first group to others
        # Create folder for each section the brres has
        for i in range(len(self.folders)):
            folder = self.folders[i]
            size = len(folder)
            if size:
                f = Folder(binfile, self.FOLDERS[i])
                for j in range(size):
                    f.addEntry(folder[j].name)  # might not have name?
                rootFolder.addEntry(f.name)
                rootFolders.append(f)
                offsets.append(byteSize)
                byteSize += f.byteSize()
        # now update the dataptrs
        rtsize = rootFolder.byteSize()
        entries = rootFolder.entries
        for i in range(len(offsets)):
            entries[i].dataPtr = offsets[i] + rtsize
        byteSize += rtsize + 8  # add first folder to bytesize, and header len
        return rootFolders, byteSize

    def packRoot(self, binfile, root):
        """ Packs the root section, returns root folders that need data ptrs"""
        binfile.writeMagic("root")
        rtFolders, rtSize = root[0], root[1]
        binfile.write("I", rtSize)
        for f in rtFolders:
            f.pack(binfile)
        return rtFolders[1:]

    def pack(self, binfile):
        """ packs the brres """
        binfile.start()
        root = self.generateRoot(binfile)
        binfile.writeMagic(self.MAGIC)
        binfile.write("H", 0xfeff)  # BOM
        binfile.advance(2)
        binfile.markLen()
        num_sections = self.getNumSections(root[0])
        binfile.write("2H", 0x10, num_sections)
        folders = self.packRoot(binfile, root)
        # now pack the folders
        folder_index = 0
        for subfolder in self.folders:
            if len(subfolder):
                refGroup = folders[folder_index]
                for file in subfolder:
                    refGroup.createEntryRefI()  # create the dataptr
                    file.pack(binfile)
                folder_index += 1
        binfile.packNames()
        binfile.align()
        binfile.end()
    # --------------------------------------------------------------------------
