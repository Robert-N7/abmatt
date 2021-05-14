import os
import string

from abmatt.autofix import AutoFix
from abmatt.brres.chr0 import Chr0
from abmatt.brres.clr0.clr0 import Clr0
from abmatt.brres.lib.binfile import Folder, UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.brres.pat0.pat0 import Pat0Collection, Pat0
from abmatt.brres.scn0.scn0 import Scn0
from abmatt.brres.shp0.shp0 import Shp0
from abmatt.brres.srt0.srt0 import SRTCollection, Srt0
from abmatt.brres.tex0 import Tex0


class UnpackBrres(Unpacker):

    @staticmethod
    def create_model_animation_map(animations, model_names):
        model_anim_map = {}  # dictionary of model names to animations
        if animations:
            for x in animations:
                name = x.name   # first try just the name no change
                if name not in model_names:
                    name = name.rstrip(string.digits)   # strip digits
                if not model_anim_map.get(name):
                    model_anim_map[name] = [x]
                else:
                    model_anim_map[name].append(x)
        return model_anim_map

    def generate_srt_collections(self, srt0_anims):
        # srt animation processing
        brres = self.node
        model_names = {x.name for x in brres.models}
        model_anim_map = self.create_model_animation_map(srt0_anims, model_names)
        # now create SRT Collection
        anim_collections = []
        for key in model_anim_map:
            collection = SRTCollection(key, brres, model_anim_map[key])
            anim_collections.append(collection)
            mdl = brres.get_model(key)
            if not mdl:
                AutoFix.info('No model found matching srt0 animation {} in {}'.format(key, brres.name), 3)
            else:
                mdl.set_srt0(collection)
        return anim_collections

    def generate_pat0_collections(self, pat0_anims):
        brres = self.node
        model_names = {x.name for x in brres.models}
        model_anim_map = self.create_model_animation_map(pat0_anims, model_names)
        # now create PAT0 Collection
        anim_collections = []
        for key in model_anim_map:
            collection = Pat0Collection(key, brres, model_anim_map[key])
            anim_collections.append(collection)
            mdl = brres.get_model(key)
            if not mdl:
                AutoFix.info('No model found matching pat0 animation {} in {}'.format(key, brres.name), 3)
            else:
                mdl.set_pat0(collection)
        return anim_collections

    def post_unpacking(self, brres):
        for x in brres.textures:
            brres.texture_map[x.name] = x
        brres.pat0 = self.generate_pat0_collections(brres.pat0) if brres.pat0 else []
        brres.srt0 = self.generate_srt_collections(brres.srt0) if brres.srt0 else []

    def unpack(self, brres, binfile):
        """ Unpacks the brres """
        binfile.start()
        magic = binfile.readMagic()
        if magic != 'bres':
            raise UnpackingError(brres, '"{}" not a brres file'.format(brres.name))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        binfile.advance(2)
        binfile.readLen()
        rootoffset, numSections = binfile.read("2h", 4)
        binfile.offset = rootoffset
        root = binfile.readMagic()
        assert (root == 'root')
        section_length = binfile.read("I", 4)
        self.root = root = Folder(binfile, root)
        root.unpack(binfile)
        # open all the folders
        for i in range(len(root)):
            self.unpack_folder(root.recallEntryI())
        binfile.end()
        self.post_unpacking(brres)

    def unpack_subfiles(self, klass):
        subfolder = Folder(self.binfile, self.folder_name)
        subfolder.unpack(self.binfile)
        return [klass(subfolder.recallEntryI(), self.node, self.binfile) for i in range(len(subfolder))]

    def unpack_folder(self, folder_name):
        self.folder_name = folder_name
        if folder_name == "3DModels(NW4R)":
            self.node.models = self.unpack_subfiles(Mdl0)
        elif folder_name == "Textures(NW4R)":
            self.node.textures = self.unpack_subfiles(Tex0)
        elif folder_name == "AnmTexPat(NW4R)":
            self.node.pat0 = self.unpack_subfiles(Pat0)
        elif folder_name == "AnmTexSrt(NW4R)":
            self.node.srt0 = self.unpack_subfiles(Srt0)
        elif folder_name == "AnmChr(NW4R)":
            self.node.chr0 = self.unpack_subfiles(Chr0)
        elif folder_name == "AnmScn(NW4R)":
            self.node.scn0 = self.unpack_subfiles(Scn0)
        elif folder_name == "AnmShp(NW4R)":
            self.node.shp0 = self.unpack_subfiles(Shp0)
        elif folder_name == "AnmClr(NW4R)":
            self.node.clr0 = self.unpack_subfiles(Clr0)
        else:
            raise UnpackingError(self.binfile, 'Unkown folder {}'.format(folder_name))