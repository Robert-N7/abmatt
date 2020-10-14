import string

from autofix import AutoFix
from brres.lib.binfile import Folder, UnpackingError
from brres.lib.unpacking.interface import Unpacker
from brres.pat0.pat0 import Pat0Collection
from brres.srt0.srt0 import SRTCollection


class UnpackBrres(Unpacker):
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
        while len(root):
            container = []
            folder_name = root.recallEntryI()
            klass = brres.FOLDERS[folder_name]
            subFolder = Folder(binfile, folder_name)
            subFolder.unpack(binfile)
            while len(subFolder):
                name = subFolder.recallEntryI()
                container.append(klass(name, brres, binfile))
            brres.folders[folder_name] = container
        binfile.end()
        self.post_unpacking(brres)
