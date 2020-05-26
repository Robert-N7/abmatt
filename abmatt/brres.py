#!/usr/bin/python
#--------------------------------------------------------
#   Brres Class
#--------------------------------------------------------
import sys
import os
import binascii
sys.path.insert(1, 'mdl0')
sys.path.insert(1, 'srt0')
sys.path.insert(1, 'mdl0/wiigraphics')
from mdl0 import *
from subfile import *
from srt0 import *
from material import *
from layer import *
from shader import *
from binfile import BinFile


class Brres():
    FOLDERS = ["3DModels(NW4R)", "Textures(NW4R)", "AnmTexSrt(NW4R)", "AnmChr(NW4R)",
                "AnmTexPat(NW4R)", "AnmScn(NW4R)", "AnmShp(NW4R)", "AnmClr(NW4R)"]
    CLASSES = [Mdl0, Tex0, Srt0, Chr0, Pat0, Scn0, Shp0, Clr0]
    MAGIC = "bres"
    ROOTMAGIC = "root"

    def __init__(self, name, parent=None, readFile = True):
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
        self.folders = [self.models, self.textures, self.anmSrt, self.anmChr,
                        self.anmPat, self.anmClr, self.anmShp, self.anmScn]
        self.isModified = False
        self.isUpdated = False
        self.parent = parent
        self.name = name
        if readFile:
            self.unpack(BinFile(self.name))

    def getModelsByName(self, name):
        return findAll(name, self.models)

    def save(self, filename, overwrite):
        if not filename:
            filename = self.name
            if not self.isChanged():
                return
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            binfilefile = binfile(filename, mode="w")
            self.pack(binfilefile)
            binfilefile.commitWrite()
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

    def getNumSections(self):
        ''' gets the number of sections, including root'''
        count = 1 # root
        for x in self.folders:
            if x:
                count += 1
        return count

    # -------------------------------------------------------------------------
    #   PACKING / UNPACKING
    # -------------------------------------------------------------------------
    def unpackFolder(self, binfile, root, folderIndex):
        ''' Unpacks the folder folderIndex '''
        name = self.FOLDERS[folderIndex]
        if root.open(name):
            if __debug__:
                print("Opened folder {}".format(name))
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
        ''' Unpacks the brres '''
        if __debug__:
            print("Unpacking brres {}".format(self.name))
        binfile.start()
        magic = binfile.readMagic()
        if magic != self.MAGIC:
            raise ValueError("Magic {} does not match {}".format(magic, self.MAGIC))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        pad, self.length, rootoffset, self.numSections = binfile.read("hI2h", 10)
        binfile.offset = rootoffset
        root = binfile.readMagic()
        assert(root == self.ROOTMAGIC)
        sectionLength = binfile.read("I", 4)
        root = Folder(binfile, root)
        root.unpack(binfile)
        if __debug__:
            print("{} folders detected".format(len(root)))
        # open all the folders
        for i in range(len(self.FOLDERS)):
            self.unpackFolder(binfile, root, i)
        if __debug__:
            print("Finished unpacking brres.")
        binfile.end()

    def generateRoot(self, binfile):
        ''' Generates the root folders
            Does not hook up data pointers except the head group,
            returns (rootFolders, bytesize)
        '''
        rootFolders = [] # for storing Index Groups
        byteSize = 0
        # Create folder indexing folders
        rootFolder = Folder(binfile, self.ROOTMAGIC)
        rootFolders.append(rootFolder)
        offsets = []    # for tracking offsets from first group to others
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
        byteSize += rtsize + 8  # add first folder to bytsize, and header len
        return rootFolders, bytesize

    def packRoot(self, binfile):
        ''' Packs the root section, returns root folders that need data ptrs'''
        binfile.start()
        binfile.writeMagic("root")
        rtFolders, rtSize = self.generateRoot(binfile)
        binfile.write("I", rtsize)
        for f in rtFolders:
            f.pack()
        binfile.end()
        return rtFolders[1:]

    def pack(self, binfile):
        ''' packs the brres '''
        binfile.start()
        binfile.writeMagic(self.MAGIC)
        binfile.write("H", 0xfffe)   # BOM
        binfile.advance(2)
        binfile.markLen()
        numSections = self.getNumSections()
        binfile.write("2H", 0x10, numSections)
        folders = self.packRoot(binfile)
        # now pack the folders
        folderIndex = 0
        for subfolder in self.folders:
            if len(subfolder):
                refGroup = folders[folderIndex]
                for file in subfolder:
                    refGroup.createEntryRefI()  # create the dataptr
                    entry.pack(binfile)
                folderIndex += 1
        binfile.packNames()
        binfile.end()
    # --------------------------------------------------------------------------
