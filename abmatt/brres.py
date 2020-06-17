#!/usr/bin/python
# --------------------------------------------------------
#   Brres Class
# --------------------------------------------------------
import os
import re
import string
import sys

from abmatt.binfile import BinFile, Folder, UnpackingError
from abmatt.layer import Layer
from abmatt.matching import findAll
from abmatt.mdl0 import Mdl0
from abmatt.pat0 import Pat0
from abmatt.srt0 import Srt0, SRTCollection
from abmatt.subfile import *


class Brres():
    FOLDERS = ["3DModels(NW4R)", "Textures(NW4R)", "AnmTexPat(NW4R)", "AnmTexSrt(NW4R)", "AnmChr(NW4R)",
               "AnmScn(NW4R)", "AnmShp(NW4R)", "AnmClr(NW4R)"]
    CLASSES = [Mdl0, Tex0, Pat0, Srt0, Chr0, Scn0, Shp0, Clr0]
    SETTINGS = ('name')
    MAGIC = "bres"
    ROOTMAGIC = "root"
    OVERWRITE = False
    DESTINATION = None

    def __init__(self, name, parent=None, readFile=True):
        """
            initialize brres
            name - the brres name, or filename
            parent - optional for supporting containing files in future
            readfile - optional start reading and unpacking file
        """
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

    def __getitem__(self, key):
        if key == 'name':
            return self.name
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def __setitem__(self, key, value):
        if key == 'name':
            self.name = value
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def close(self):
        if self.isModified or self.DESTINATION and self.DESTINATION != self.name:
            self.save(self.DESTINATION, self.OVERWRITE)

    def save(self, filename, overwrite):
        if not filename:
            filename = self.name
            # if not self.isChanged():
            #     return
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            f = BinFile(filename, mode="w")
            self.pack(f)
            f.commitWrite()
            print("Wrote file '{}'".format(filename))
            self.name = filename
            self.isModified = False
            return True

    def getTrace(self):
        if self.parent:
            return self.parent.name + "->" + self.name
        return self.name

    def info(self, key=None, indentation_level=0):
        print('{}{}:\t{} model(s)\t{} texture(s)'.format('  ' * indentation_level + '>', self.name,
                                                         len(self.models), len(self.textures)))
        folder_indent = indentation_level + 1
        indentation_level += 2
        folders = self.folders
        for i in range(len(folders)):
            folder = folders[i]
            if folder:
                print('{}>{}'.format('  ' * folder_indent, self.FOLDERS[i]))
                for x in folder:
                    x.info(key, indentation_level)

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
        count = 1  # root
        for x in folders[count:]:
            if x:
                count += len(x)
                # print('Length of folder {} is {}'.format(x.name, len(x)))
        return count

    # ------------------------------ Models ---------------------------------

    def getModel(self, name):
        for x in self.models:
            if x.name == name:
                return x

    def getExpectedMdl(self):
        filename = os.path.basename(self.name)
        if filename in ('course_model', 'map_model', 'vrcorn_model'):
            return filename.replace('_model', '')

    def updateModelName(self, old_name, new_name):
        for folder in self.folders[2:]:
            for x in folder:
                if old_name in x.name:
                    x.name = x.name.replace(old_name, new_name)

    def getModelsByName(self, name):
        return findAll(name, self.models)

    # -------------------------------- Textures -----------------------------

    def getTexture(self, name):
        for x in self.textures:
            if x.name == name:
                return x

    def getTextures(self, name):
        return findAll(name, self.textures)

    # --------------------- SRT0 ----------------------------------------------
    def generate_srt_collections(self):
        # srt animation processing
        animations = self.anmSrt
        model_anim_map = {}  # dictionary of model names to animations
        if animations:
            for x in animations:
                name = x.name.rstrip(string.digits)
                if not model_anim_map.get(name):
                    model_anim_map[name] = [x]
                else:
                    model_anim_map[name].append(x)
            # now create SRT Collection
            for key, val in enumerate(model_anim_map):
                mdl = self.getModel(key)
                if not mdl:
                    print('Warning: No model found matching animation {}'.format(key))
                else:
                    mdl.set_srt0(SRTCollection(key, self, val))

    def get_srt0s_for_packing(self):
        # srt animation processing
        animations = []
        for mdl in self.models:
            if mdl.srt0_collection:
                animations.extend(mdl.srt0_collection.consolidate())
        return animations

    # -------------------------------------------------------------------------
    #   PACKING / UNPACKING
    # -------------------------------------------------------------------------
    def post_unpacking(self):
        self.generate_srt_collections()

    def pre_packing(self):
        self.folders[3] = self.get_srt0s_for_packing()

    def unpackFolder(self, binfile, root, folderIndex):
        """ Unpacks the folder folderIndex """
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
            raise UnpackingError(self, "Magic {} does not match {}".format(magic, self.MAGIC))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        pad, length, rootoffset, numSections = binfile.read("hI2h", 10)
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
        self.post_unpacking()

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
        self.pre_packing()
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
