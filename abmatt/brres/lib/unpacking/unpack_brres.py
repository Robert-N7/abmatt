import string

from autofix import AutoFix
from brres.chr0 import Chr0
from brres.clr0.clr0 import Clr0
from brres.lib.binfile import Folder, UnpackingError
from brres.lib.unpacking.interface import Unpacker
from brres.mdl0.mdl0 import Mdl0
from brres.pat0.pat0 import Pat0Collection, Pat0
from brres.scn0.scn0 import Scn0
from brres.shp0.shp0 import Shp0
from brres.srt0.srt0 import SRTCollection, Srt0
from brres.tex0 import Tex0


class UnpackBrres(Unpacker):
    FOLDERS = {}

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

    def generate_srt_collections(self, srt0_anims):
        # srt animation processing
        brres = self.node
        model_anim_map = self.create_model_animation_map(srt0_anims)
        # now create SRT Collection
        anim_collections = []
        for key in model_anim_map:
            collection = SRTCollection(key, brres, model_anim_map[key])
            anim_collections.append(collection)
            mdl = brres.getModel(key)
            if not mdl:
                AutoFix.get().info('No model found matching srt0 animation {}'.format(key), 3)
            else:
                mdl.set_srt0(collection)
        return anim_collections

    def generate_pat0_collections(self, pat0_anims):
        brres = self.node
        model_anim_map = self.create_model_animation_map(pat0_anims)
        # now create PAT0 Collection
        anim_collections = []
        for key in model_anim_map:
            collection = Pat0Collection(key, brres, model_anim_map[key])
            anim_collections.append(collection)
            mdl = brres.getModel(key)
            if not mdl:
                AutoFix.get().info('No model found matching pat0 animation {}'.format(key), 3)
            else:
                mdl.set_pat0(collection)
        return anim_collections

    def post_unpacking(self, brres):
        mdl_name = brres.ORDERED[0]
        x = brres.folders.get(mdl_name)
        brres.folders[mdl_name] = brres.models = x if x else []
        tex_name = brres.ORDERED[1]
        x = brres.folders.get(tex_name)
        brres.folders[tex_name] = brres.textures = x if x else []
        for x in brres.textures:
            brres.texture_map[x.name] = x
        x = brres.folders.get("AnmTexPat(NW4R)")
        brres.folders["AnmTexPat(NW4R)"] = brres.pat0 = self.generate_pat0_collections(x) if x else []
        x = brres.folders.get("AnmTexSrt(NW4R)")
        brres.folders["AnmTexSrt(NW4R)"] = brres.srt0 = self.generate_srt_collections(x) if x else []

    def unpack(self, brres, binfile):
        """ Unpacks the brres """
        binfile.start()
        magic = binfile.readMagic()
        if magic != brres.MAGIC:
            raise UnpackingError(brres, '"{}" not a brres file'.format(brres.name))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        binfile.advance(2)
        binfile.readLen()
        rootoffset, numSections = binfile.read("2h", 4)
        binfile.offset = rootoffset
        root = binfile.readMagic()
        assert (root == brres.ROOTMAGIC)
        section_length = binfile.read("I", 4)
        root = Folder(binfile, root)
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


    def unpack_models(self):
        self.node.models = self.unpack_subfiles(Mdl0)

    def unpack_textures(self):
        self.node.textures = self.unpack_subfiles(Tex0)

    def unpack_pat0(self):
        self.node.pat0 = self.unpack_subfiles(Pat0)

    def unpack_srt0(self):
        self.node.srt0 = self.unpack_subfiles(Srt0)

    def unpack_chr0(self):
        self.node.chr0 = self.unpack_subfiles(Chr0)

    def unpack_scn0(self):
        self.node.scn0 = self.unpack_subfiles(Scn0)

    def unpack_shp0(self):
        self.node.shp0 = self.unpack_subfiles(Shp0)

    def unpack_clr0(self):
        self.node.clr0 = self.unpack_subfiles(Clr0)

    def unpack_folder(self, folder_name):
        self.folder_name = folder_name
        if folder_name == "3DModels(NW4R)":
            self.unpack_models()
        elif folder_name == "Textures(NW4R)":
            self.unpack_textures()
        elif folder_name == "AnmTexPat(NW4R)":
            self.unpack_pat0()
        elif folder_name == "AnmTexSrt(NW4R)":
            self.unpack_srt0()
        elif folder_name == "AnmChr(NW4R)":
            self.unpack_chr0()
        elif folder_name == "AnmScn(NW4R)":
            self.unpack_scn0()
        elif folder_name == "AnmShp(NW4R)":
            self.unpack_shp0()
        elif folder_name == "AnmClr(NW4R)":
            self.unpack_clr0()