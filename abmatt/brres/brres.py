#!/usr/bin/python
# --------------------------------------------------------
#   Brres Class
# --------------------------------------------------------
import os
import string

from brres.lib.autofix import AUTO_FIXER, Bug
from brres.lib.binfile import BinFile, Folder, UnpackingError
from brres.chr0 import Chr0
from brres.clr0 import Clr0
from brres.lib.matching import MATCHING
from brres.lib.node import Clipable
from brres.mdl0 import Mdl0
from brres.pat0 import Pat0, Pat0Collection
from brres.scn0 import Scn0
from brres.shp0 import Shp0
from brres.srt0 import Srt0, SRTCollection
from brres.tex0 import Tex0, ImgConverter


class Brres(Clipable):
    FOLDERS = {"3DModels(NW4R)": Mdl0,
               "Textures(NW4R)": Tex0,
               "AnmTexPat(NW4R)": Pat0,
               "AnmTexSrt(NW4R)": Srt0,
               "AnmChr(NW4R)": Chr0,
               "AnmScn(NW4R)": Scn0,
               "AnmShp(NW4R)": Shp0,
               "AnmClr(NW4R)": Clr0}
    ANIM_COLLECTIONS = ("AnmTexPat(NW4R)", "AnmTexSrt(NW4R)")
    ORDERED = ("3DModels(NW4R)", "Textures(NW4R)")
    SETTINGS = ('name')
    MAGIC = "bres"
    ROOTMAGIC = "root"
    OVERWRITE = False
    DESTINATION = None
    OPEN_FILES = None  # reference to active files
    REMOVE_UNUSED_TEXTURES = False

    def __init__(self, name, parent=None, readFile=True):
        """
            initialize brres
            name - the brres name, or filename
            parent - optional for supporting containing files in future
            readfile - optional start reading and unpacking file
        """
        self.folders = {}
        self.isModified = False
        self.texture_map = {}
        binfile = BinFile(self.name) if readFile else None
        super(Brres, self).__init__(name, parent, binfile)

    def begin(self):
        folders = self.folders
        self.models = folders[self.ORDERED[0]] = []
        self.textures = folders[self.ORDERED[1]] = []
        self.pat0 = folders[self.ANIM_COLLECTIONS[0]] = []
        self.srt0 = folders[self.ANIM_COLLECTIONS[1]] = []

    def get_str(self, key):
        if key == 'name':
            return self.name
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def set_str(self, key, value):
        if key == 'name':
            self.name = value
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def import_model(self, file_path):
        from converters.dae_convert import DaeConverter
        converter = DaeConverter(self, file_path)
        converter.load_model()

    def add_mdl0(self, mdl0):
        prev = self.getModel(mdl0.name)
        if prev:
            self.models.remove(prev)
            mdl0.paste(prev)
        self.models.append(mdl0)
        mdl0.link_parent(self)
        return mdl0

    def remove_mdl0(self, name):
        for x in self.models:
            if x.name == name:
                self.models.remove(x)
                break

    def remove_mdl0_i(self, i):
        self.models.pop(i)

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
            AUTO_FIXER.error('File {} already exists!'.format(filename), 1)
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
        for folder_name in folders:
            folder = folders[folder_name]
            folder_len = len(folder)
            if folder_len:
                print('{}>{}\t{}'.format('  ' * folder_indent, folder_name, folder_len))
                for x in folder:
                    x.info(key, indentation_level)

    def isChanged(self):
        return self.isModified

    # ------------------------------ Models ---------------------------------

    def getModel(self, name):
        for x in self.models:
            if x.name == name:
                return x

    def getModelI(self, i=0):
        try:
            return self.models[i]
        except IndexError:
            pass

    def getExpectedMdl(self):
        filename = self.name
        for item in ('course', 'map', 'vrcorn'):
            if item in filename:
                return item

    def renameModel(self, old_name, new_name):
        for x in self.models:
            if x.name == new_name:
                AUTO_FIXER.warn('Unable to rename {}, the model {} already exists!'.format(old_name, new_name))
                return None
        folders = self.folders
        for n in folders:
            for x in folders[n]:
                if old_name == x.name:  # possible bug... model animations with similar names may be renamed
                    x.name = new_name
            return new_name

    def getModelsByName(self, name):
        return MATCHING.findAll(name, self.models)

    # -------------------------------- Textures -----------------------------
    def findTexture(self, name):
        """Attempts to find the texture by name"""
        if not self.OPEN_FILES:
            return None
        for x in self.OPEN_FILES:
            if x is not self:
                tex = x.getTexture(name)
                if tex is not None:
                    return tex

    def add_tex0(self, tex0):
        if tex0.name in self.texture_map:
            self.remove_tex0(tex0.name)
            AUTO_FIXER.info('Replaced tex0 {}'.format(tex0.name))
        self.textures.append(tex0)
        self.texture_map[tex0.name] = tex0

    def paste_tex0s(self, brres):
        tex_map = brres.texture_map
        for x in tex_map:
            self.add_tex0(tex_map[x])

    def import_texture(self, image_path):
        tex0 = ImgConverter().encode(image_path)
        if tex0:
            self.add_tex0(tex0)
        return tex0

    def rename_texture(self, tex0, name):
        self.texture_map[tex0.name] = None
        tex0.name = name
        self.texture_map[tex0.name] = tex0

    def get_texture_map(self):
        return self.texture_map

    def getTexture(self, name):
        tex = self.get_texture_map().get(name)
        if tex is None:
            tex = self.findTexture(name)
            if tex:
                self.add_tex0(tex)
        return tex

    def hasTexture(self, name):
        return True if name in self.texture_map else False

    def getTextures(self, name):
        return MATCHING.findAll(name, self.textures)

    def remove_tex0(self, name):
        try:
            tex = self.texture_map.pop(name)
            self.textures.remove(tex)
        except KeyError:
            AUTO_FIXER.warn('No texture {} in {}'.format(name, self.name))

    def remove_tex0_i(self, i):
        tex = self.textures.pop(i)
        if tex:
            self.texture_map.pop(tex.name)

    def getUsedTextures(self):
        ret = set()
        for x in self.models:
            ret |= x.get_used_textures()
        for x in self.pat0:
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
        self.srt0.append(collection)
        return collection

    def add_pat0_collection(self, collection):
        self.pat0.append(collection)
        return collection

    def generate_srt_collections(self):
        # srt animation processing
        model_anim_map = self.create_model_animation_map(self.srt0)
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
        model_anim_map = self.create_model_animation_map(self.pat0)
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
        x = self.folders.get("AnmTexPat(NW4R)")
        self.folders["AnmTexPat(NW4R)"] = self.pat0 = self.generate_pat0_collections() if x else []
        x = self.folders.get("AnmTexSrt(NW4R)")
        self.folders["AnmTexSrt(NW4R)"] = self.srt0 = self.generate_srt_collections() if x else []
        mdl_name = self.ORDERED[0]
        x = self.folders.get(mdl_name)
        self.folders[mdl_name] = self.models = x if x else []
        tex_name = self.ORDERED[1]
        x = self.folders.get(tex_name)
        self.folders[tex_name] = self.textures = x if x else []
        for x in self.textures:
            self.texture_map[x.name] = x

    def pre_packing(self):
        self.check()
        folders = self.folders
        ret = []
        ordered = self.ORDERED
        anim_collect = self.ANIM_COLLECTIONS
        added = set()
        for folder in ordered:
            x = folders.get(folder)
            if x:
                ret.append((folder, x))
                added.add(folder)
        for folder in anim_collect:
            x = folders.get(folder)
            if x:
                ret.append((folder, self.get_anim_for_packing(x)))
                added.add(folder)
        for x in folders:
            if x not in added:
                ret.append((x, folders[x]))
        return ret

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
        while len(root):
            container = []
            folder_name = root.recallEntryI()
            klass = self.FOLDERS[folder_name]
            subFolder = Folder(binfile, folder_name)
            subFolder.unpack(binfile)
            while len(subFolder):
                name = subFolder.recallEntryI()
                container.append(klass(name, self, binfile))
            self.folders[folder_name] = container
        binfile.end()
        self.post_unpacking()

    @staticmethod
    def getNumSections(folders):
        """ gets the number of sections, including root"""
        count = 1  # root
        for x in folders[count:]:
            if x:
                count += len(x)
                # print('Length of folder {} is {}'.format(x.name, len(x)))
        return count

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
            folder_name, folder = subfiles[i]
            size = len(folder)
            if size:
                f = Folder(binfile, folder_name)
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
        for name, file_group in sub_files:
            if len(file_group):
                index_group = folders[folder_index]
                for file in file_group:
                    index_group.createEntryRefI()  # create the dataptr
                    file.pack(binfile)
                folder_index += 1
        binfile.packNames()
        binfile.end()

    # --------------------------------------------------------------------------
    def check(self):
        AUTO_FIXER.info('checking file {}'.format(self.name), 4)
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
