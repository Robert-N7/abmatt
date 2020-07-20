#!/usr/bin/python
# --------------------------------------------------------
#   Brres Class
# --------------------------------------------------------
import os
import string

from abmatt.autofix import AUTO_FIXER, Bug
from abmatt.binfile import BinFile, Folder, UnpackingError
from abmatt.chr0 import Chr0
from abmatt.clr0 import Clr0
from abmatt.matching import Clipable, MATCHING
from abmatt.mdl0 import Mdl0
from abmatt.pat0 import Pat0, Pat0Collection
from abmatt.scn0 import Scn0
from abmatt.shp0 import Shp0
from abmatt.srt0 import Srt0, SRTCollection
from abmatt.tex0 import Tex0


class Brres(Clipable):
    FOLDERS = ["3DModels(NW4R)", "Textures(NW4R)", "AnmTexPat(NW4R)", "AnmTexSrt(NW4R)", "AnmChr(NW4R)",
               "AnmScn(NW4R)", "AnmShp(NW4R)", "AnmClr(NW4R)"]
    CLASSES = [Mdl0, Tex0, Pat0, Srt0, Chr0, Scn0, Shp0, Clr0]
    SETTINGS = ('name')
    MAGIC = "bres"
    ROOTMAGIC = "root"
    OVERWRITE = False
    DESTINATION = None
    ACTIVE_FILES = None     # reference to active files
    REMOVE_UNUSED_TEXTURES=False

    def __init__(self, name, parent=None, readFile=True):
        """
            initialize brres
            name - the brres name, or filename
            parent - optional for supporting containing files in future
            readfile - optional start reading and unpacking file
        """
        super(Brres, self).__init__(name, parent)
        self.models = []
        self.textures = []
        self.anmSrt = []
        self.anmChr = []
        self.anmPat = []
        self.anmClr = []
        self.anmShp = []
        self.anmScn = []
        self.folders = [self.models, self.textures, self.anmPat, self.anmSrt, self.anmChr,
                        self.anmScn, self.anmShp, self.anmClr]
        self.isModified = False
        self.isUpdated = False
        self.parent = parent
        self.name = name
        self.texture_map = None
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

    # ---------------------------------------------- CLIPBOARD ------------------------------------------
    def paste(self, brres):
        self.paste_group(self.models, brres.models)
        # textures
        t1 = self.get_texture_map()
        t2 = brres.get_texture_map()
        for x in t2:
            tex = t1.get(x)
            if tex:
                tex.paste(t2[x])
        # todo chr0 paste


    def mark_modified(self):
        self.isModified = True

    # -------------------------- SAVE/ CLOSE --------------------------------------------
    def close(self):
        if self.isModified or self.DESTINATION and self.DESTINATION != self.name:
            return self.save(self.DESTINATION, self.OVERWRITE)
        return True

    def save(self, filename, overwrite):
        if not filename:
            filename = self.name
            # if not self.isChanged():
            #     return
        if not overwrite and os.path.exists(filename):
            AUTO_FIXER.warn('File {} already exists!'.format(filename), 2)
            return False
        else:
            f = BinFile(filename, mode="w")
            self.pack(f)
            if f.commitWrite():
                AUTO_FIXER.info("Wrote file '{}'".format(filename), 2)
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
        filename = os.path.splitext(os.path.basename(self.name))[0]
        if filename in ('course_model', 'map_model', 'vrcorn_model'):
            return filename.replace('_model', '')

    def updateModelName(self, old_name, new_name):
        for folder in self.folders[2:]:
            for x in folder:
                if old_name == x.name:      # possible bug... model animations with similar names may be renamed
                    x.name = x.name.replace(old_name, new_name)

    def getModelsByName(self, name):
        return MATCHING.findAll(name, self.models)

    # -------------------------------- Textures -----------------------------
    def findTexture(self, name):
        """Attempts to find the texture by name"""
        for x in self.ACTIVE_FILES:
            if x is not self:
                tex = x.getTexture(name)
                if tex is not None:
                    return tex

    def addTexture(self, tex0):
        self.textures.append(tex0)
        self.texture_map[tex0.name] = tex0

    def get_texture_map(self):
        if not self.texture_map:
            self.texture_map = {}
            for x in self.textures:
                self.texture_map[x.name] = x
        return self.texture_map

    def getTexture(self, name):
        tex = self.get_texture_map().get(name)
        if tex is None:
            tex = self.findTexture(name)
            if tex:
                self.addTexture(tex)
        return tex

    def getTextures(self, name):
        return MATCHING.findAll(name, self.textures)

    def getUsedTextures(self):
        ret = set()
        for x in self.models:
            ret |= x.get_used_textures()
        for x in self.anmPat:
            ret |= x.get_used_textures()
        return ret

    # --------------------- Animations ----------------------------------------------
    @staticmethod
    def create_model_animation_map(animations):
        model_anim_map = {}  # dictionary of model names to animations
        if animations:
            for x in animations:
                name = x.name.rstrip(string.digits)
                if not model_anim_map.get(name):
                    model_anim_map[name] = [x]
                else:
                    model_anim_map[name].append(x)
        return model_anim_map

    @staticmethod
    def get_anim_for_packing(anim_collection):
        # srt animation processing
        animations = []
        for x in anim_collection:
            animations.extend(x.consolidate())
        return animations

    def add_srt_collection(self, collection):
        self.anmSrt.append(collection)
        return collection

    def add_pat0_collection(self, collection):
        self.anmPat.append(collection)
        return collection

    def generate_srt_collections(self):
        # srt animation processing
        model_anim_map = self.create_model_animation_map(self.anmSrt)
        # now create SRT Collection
        anim_collections = []
        for key in model_anim_map:
            collection = SRTCollection(key, self, model_anim_map[key])
            anim_collections.append(collection)
            mdl = self.getModel(key)
            if not mdl:
                AUTO_FIXER.info('No model found matching srt0 animation {}'.format(key), 3)
            else:
                mdl.set_srt0(collection)
        return anim_collections

    def generate_pat0_collections(self):
        model_anim_map = self.create_model_animation_map(self.anmPat)
        # now create SRT Collection
        anim_collections = []
        for key in model_anim_map:
            collection = Pat0Collection(key, self, model_anim_map[key])
            anim_collections.append(collection)
            mdl = self.getModel(key)
            if not mdl:
                AUTO_FIXER.info('No model found matching pat0 animation {}'.format(key), 3)
            else:
                mdl.set_pat0(collection)
        return anim_collections

    # -------------------------------------------------------------------------
    #   PACKING / UNPACKING
    # -------------------------------------------------------------------------
    def post_unpacking(self):
        self.folders[2] = self.anmPat = self.generate_pat0_collections()
        self.folders[3] = self.anmSrt = self.generate_srt_collections()

    def pre_packing(self):
        self.check()
        folders = [x for x in self.folders]
        folders[2] = self.get_anim_for_packing(self.anmPat)
        folders[3] = self.get_anim_for_packing(self.anmSrt)
        return folders

    def unpackFolder(self, binfile, root, folderIndex):
        """ Unpacks the folder folderIndex """
        name = self.FOLDERS[folderIndex]
        if root.open(name):
            container = self.folders[folderIndex]
            subFolder = Folder(binfile, name)
            # print('Folder {} at {}'.format(name, binfile.offset))
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
            raise UnpackingError(self, '"{}" not a brres file'.format(self.name))
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

    def generateRoot(self, binfile, subfiles):
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
        for i in range(len(subfiles)):
            folder = subfiles[i]
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
        return rootFolders

    @staticmethod
    def packRoot(binfile, rt_folders):
        """ Packs the root section, returns root folders that need data ptrs"""
        binfile.start()
        binfile.writeMagic("root")
        binfile.markLen()
        for f in rt_folders:
            f.pack(binfile)
        binfile.end()
        binfile.align()
        return rt_folders[1:]

    def pack(self, binfile):
        """ packs the brres """
        sub_files = self.pre_packing()
        binfile.start()
        rt_folders = self.generateRoot(binfile, sub_files)
        binfile.writeMagic(self.MAGIC)
        binfile.write("H", 0xfeff)  # BOM
        binfile.advance(2)
        binfile.markLen()
        num_sections = self.getNumSections(rt_folders)
        binfile.write("2H", 0x10, num_sections)
        folders = self.packRoot(binfile, rt_folders)
        # now pack the folders
        folder_index = 0
        for file_group in sub_files:
            if len(file_group):
                index_group = folders[folder_index]
                for file in file_group:
                    index_group.createEntryRefI()  # create the dataptr
                    file.pack(binfile)
                folder_index += 1
        binfile.packNames()
        binfile.align()
        binfile.end()

    # --------------------------------------------------------------------------
    def check(self):
        AUTO_FIXER.info('checking file {}'.format(self.name), 3)
        for mdl in self.models:
            mdl.check()
        tex_names = set(self.get_texture_map().keys())
        tex_used = self.getUsedTextures()
        unused = tex_names - tex_used
        if unused:
            b = Bug(4, 3, 'Unused textures: {}'.format(unused), 'Remove textures')
            if self.REMOVE_UNUSED_TEXTURES:
                self.remove_unused_textures(unused)
                b.resolve()
                self.mark_modified()
        for x in self.textures:
            x.check()

    def remove_unused_textures(self, unused_textures):
        tex = self.textures
        tex_map = self.texture_map
        for x in unused_textures:
            tex.remove(tex_map.pop(x))
