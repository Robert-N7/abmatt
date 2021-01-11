#!/usr/bin/python
# --------------------------------------------------------
#   Brres Class
# --------------------------------------------------------
import os

from abmatt.autofix import AutoFix, Bug
from abmatt.brres.lib.binfile import BinFile
from abmatt.brres.lib.matching import MATCHING
from abmatt.brres.lib.node import Clipable, Packable
from abmatt.brres.lib.packing.pack_brres import PackBrres
from abmatt.brres.lib.unpacking.unpack_brres import UnpackBrres
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.tex0 import Tex0
from abmatt.image_converter import ImgConverter


class Brres(Clipable, Packable):

    SETTINGS = ('name')
    MAGIC = 'bres'
    OVERWRITE = False
    DESTINATION = None
    OPEN_FILES = []  # reference to active files
    REMOVE_UNUSED_TEXTURES = False

    def __init__(self, name, parent=None, readFile=True):
        """
            initialize brres
            name - the brres name, or filename
            parent - optional for supporting containing files in future
            readfile - optional start reading and unpacking file
        """
        # self.folders = {}
        name = os.path.abspath(name)
        self.is_modified = False
        self.has_new_model = False
        self.models = []
        self.texture_map = {}
        self.textures = []
        self.srt0 = []
        self.pat0 = []
        self.chr0 = []
        self.scn0 = []
        self.shp0 = []
        self.clr0 = []
        binfile = BinFile(name) if readFile else None
        super(Brres, self).__init__(name, parent, binfile)
        self.add_open_file(self)
        if binfile:
            self.unpack(binfile)

    def get_full_path(self):
        return self.name

    @staticmethod
    def add_open_file(file):
        Brres.OPEN_FILES.append(file)

    @staticmethod
    def close_files():
        for x in Brres.OPEN_FILES:
            x.close()
        Brres.OPEN_FILES = []

    @staticmethod
    def get_brres(filename, create_if_not_exists=False):
        filename = os.path.abspath(filename)
        for x in Brres.OPEN_FILES:
            if filename == x.name:
                return x
        if os.path.exists(filename):
            return Brres(filename, readFile=True)
        elif create_if_not_exists:
            return Brres(filename, readFile=False)

    def begin(self):
        self.is_modified = True

    def get_str(self, key):
        if key == 'name':
            return self.name
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def set_str(self, key, value):
        if key == 'name':
            self.rename(value)
        else:
            raise ValueError('Unknown key "{}"'.format(key))

    def import_model(self, file_path):
        from abmatt.converters.convert_dae import DaeConverter2
        converter = DaeConverter2(self, file_path)
        converter.load_model()
        self.mark_modified()

    def add_mdl0(self, mdl0):
        prev = self.getModel(mdl0.name)
        if prev:
            self.remove_mdl0(mdl0.name)
        self.models.append(mdl0)
        mdl0.link_parent(self)
        self.mark_modified()
        return mdl0

    def remove_mdl0(self, name):
        for x in self.models:
            if x.name == name:
                self.models.remove(x)
                if x.srt0_collection:
                    self.srt0.remove(x.srt0_collection)
                if x.pat0_collection:
                    self.pat0.remove(x.pat0_collection)
                self.mark_modified()
                break

    def remove_mdl0_i(self, i):
        self.models.pop(i)
        self.mark_modified()

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
        self.mark_modified()
        # todo chr0 paste

    def paste_material_tex0s(self, material, old_brres):
        pasted_count = 0
        if old_brres is not self:
            old_map = old_brres.texture_map
            for layer in material.layers:
                tex0 = old_map.get(layer.name)
                if tex0 is not None and layer.name not in self.texture_map:
                    t = Tex0(tex0.name, parent=self)
                    t.paste(tex0)
                    if self.add_tex0(t, False, False):
                        pasted_count += 1
        return pasted_count

    # -------------------------- SAVE/ CLOSE --------------------------------------------
    def close(self, try_save=True):
        try:
            Brres.OPEN_FILES.remove(self)
        except ValueError:
            pass
        if try_save and self.is_modified or self.DESTINATION and self.DESTINATION != self.name:
            return self.save(self.DESTINATION, self.OVERWRITE)

    def save(self, filename=None, overwrite=None, check=True):
        if not filename:
            filename = self.name
        if overwrite is None:
            overwrite = self.OVERWRITE
        if not overwrite and os.path.exists(filename):
            AutoFix.get().error('File {} already exists!'.format(filename), 1)
        else:
            if check:
                self.check()
            f = BinFile(filename, mode="w")
            self.pack(f)
            if f.commitWrite():
                AutoFix.get().info("Wrote file '{}'".format(filename), 2)
                self.rename(filename)
                self.has_new_model = False
                self.mark_unmodified()
                return True
        return False

    def get_trace(self):
        if self.parent:
            return self.parent.name + "->" + self.name
        return self.name

    def info(self, key=None, indentation_level=0):
        AutoFix.get().info('{}{}:\t{} model(s)\t{} texture(s)'.format('  ' * indentation_level + '>',
                                    self.name, len(self.models), len(self.textures)), 1)
        indentation_level += 2
        self.sub_info('MDL0', self.models, key, indentation_level)
        self.sub_info('TEX0', self.textures, key, indentation_level)
        # self.sub_info('PAT0', self.pat0, key, indentation_level)
        # self.sub_info('SRT0', self.srt0, key, indentation_level)
        self.sub_info('CHR0', self.chr0, key, indentation_level)
        self.sub_info('SCN0', self.scn0, key, indentation_level)
        self.sub_info('SHP0', self.shp0, key, indentation_level)
        self.sub_info('CLR0', self.clr0, key, indentation_level)

    def sub_info(self, folder_name, folder, key, indentation_level):
        folder_len = len(folder)
        if folder_len:
            print('{}>{}\t{}'.format('  ' * (indentation_level - 1), folder_name, folder_len))
            for x in folder:
                x.info(key, indentation_level)

    def isChanged(self):
        return self.is_modified

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

    @staticmethod
    def getExpectedBrresFileName(filename):
        dir, name = os.path.split(filename)
        name = os.path.splitext(name)[0]
        for item in ('course', 'map', 'vrcorn'):
            if item in filename:
                name = item + '_model'
                break
        return os.path.join(dir, name + '.brres')

    def getExpectedMdl(self):
        filename = self.name
        for item in ('course', 'map', 'vrcorn'):
            if item in filename:
                return item

    def get_animations(self):
        return [self.srt0, self.pat0, self.chr0, self.scn0, self.shp0, self.clr0]

    def on_model_rename(self, old_name, new_name):
        for n in self.get_animations():
            for x in n:
                if old_name == x.name:
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
                tex = x.getTexture(name, False)
                if tex is not None:
                    return tex

    def add_tex0(self, tex0, replace=True, mark_modified=True):
        if tex0.name in self.texture_map:
            if not replace:
                return False
            self.remove_tex0(tex0.name)
            AutoFix.get().info('Replaced tex0 {}'.format(tex0.name))
        if tex0.parent is not None and tex0.parent is not self:
            t = Tex0(tex0.name, self)
            t.paste(tex0)
            tex0 = t
        self.textures.append(tex0)
        self.texture_map[tex0.name] = tex0
        tex0.parent = self      # this may be redundant
        if mark_modified:
            self.mark_modified()
        return True

    def paste_tex0s(self, brres):
        tex_map = brres.texture_map
        if len(tex_map):
            for x in tex_map:
                self.add_tex0(tex_map[x], mark_modified=False)
            self.mark_modified()

    def import_texture(self, image_path, name=None):
        tex0 = ImgConverter().encode(image_path, self)
        if tex0:
            if name:
                tex0.name = name
        return tex0

    def import_textures(self, paths, tex0_format=None, num_mips=-1, check=False):
        return ImgConverter().batch_encode(paths, tex0_format, num_mips, check)

    def rename_texture(self, tex0, name):
        if tex0.rename(name):
            self.texture_map[tex0.name] = None
            self.texture_map[tex0.name] = tex0

    def get_texture_map(self):
        return self.texture_map

    def getTexture(self, name, search_other_files=True):
        tex = self.get_texture_map().get(name)
        if tex is None and search_other_files:
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
            self.mark_modified()
        except KeyError:
            AutoFix.get().warn('No texture {} in {}'.format(name, self.name))

    def remove_tex0_i(self, i):
        tex = self.textures.pop(i)
        if tex:
            self.texture_map.pop(tex.name)
            self.mark_modified()

    def getUsedTextures(self):
        ret = set()
        for x in self.models:
            ret |= x.get_used_textures()
        for x in self.pat0:
            ret |= x.get_used_textures()
        return ret

    # --------------------- Animations ----------------------------------------------

    def add_srt_collection(self, collection):
        self.srt0.append(collection)
        return collection

    def add_pat0_collection(self, collection):
        self.pat0.append(collection)
        return collection

    # -------------------------------------------------------------------------
    #   PACKING / UNPACKING
    # -------------------------------------------------------------------------

    def unpack(self, binfile):
        UnpackBrres(self, binfile)

    def pack(self, binfile):
        PackBrres(self, binfile)

    # --------------------------------------------------------------------------
    def check(self):
        AutoFix.get().info('checking file {}'.format(self.name), 4)
        expected = self.getExpectedMdl()
        for mdl in self.models:
            mdl.check(expected)
            expected = None
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

    def mark_unmodified(self):
        self.is_modified = False
        self._mark_unmodified_group(self.models)
        self._mark_unmodified_group(self.textures)
