import string

from abmatt.autofix import AutoFix
from abmatt.brres.chr0 import Chr0
from abmatt.brres.clr0.clr0 import Clr0
from abmatt.lib.binfile import Folder, UnpackingError
from abmatt.lib.unpack_interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_unknown import UnknownUnpacker
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.brres.pat0.pat0 import Pat0
from abmatt.brres.scn0.scn0 import Scn0
from abmatt.brres.shp0.shp0 import Shp0
from abmatt.brres.srt0.srt0 import Srt0
from abmatt.brres.tex0 import Tex0


class UnpackBrres(Unpacker):

    def __init__(self, node, binfile):
        self.chr0 = self.pat0 = self.srt0 = None
        self.uk_offsets = []
        super().__init__(node, binfile)

    def locate_anim_model(self, anim):
        for x in self.node.models:
            if anim.name == x.name:
                return x

    def post_unpack_anim(self, anims, model_attr, item_attr):
        if anims is None:
            return None
        anim_map = {}
        for anim in anims:
            base_name = anim.name.rstrip(string.digits) if not self.locate_anim_model(anim) else anim.name
            for x in anim:
                if anim_map.get(x.name) is None:
                    anim_map[x.name] = [x]
                else:
                    anim_map[x.name].append(x)
                x.parent_base_name = base_name
        unused = set(anim_map.keys())
        for model in self.node.models:
            for item in getattr(model, model_attr):
                anims = anim_map.get(item.name)
                if anims:
                    if len(anims) > 1:
                        for x in anims:
                            if x.parent_base_name == model.name:
                                setattr(item, item_attr, x)
                                if item.name in unused: unused.remove(item.name)
                                break
                    else:
                        setattr(item, item_attr, anims[0])
                        try:
                            unused.remove(item.name)
                        except KeyError:
                            pass
        return [y for x in unused for y in anim_map[x]]

    def post_unpacking(self, brres):
        for x in brres.textures:
            brres.texture_map[x.name] = x
        brres.unused_pat0 = self.post_unpack_anim(self.pat0, 'materials', 'pat0')
        brres.unused_srt0 = self.post_unpack_anim(self.srt0, 'materials', 'srt0')
        if brres.unused_pat0 or brres.unused_srt0:
            AutoFix.warn('Unused animations detected')

    def unpack(self, brres, binfile):
        """ Unpacks the brres """
        self.offset = binfile.start()
        magic = binfile.read_magic()
        if magic != 'bres':
            raise UnpackingError(brres, '"{}" not a brres file'.format(brres.name))
        bom = binfile.read("H", 2)
        binfile.bom = "<" if bom == 0xfffe else ">"
        binfile.advance(2)
        l = binfile.read_len()
        rootoffset, numSections = binfile.read("2h", 4)
        binfile.offset = rootoffset
        root = binfile.read_magic()
        assert (root == 'root')
        section_length = binfile.read("I", 4)
        root = Folder(binfile, root)
        root.unpack(binfile)
        self.section_offsets = []
        # open all the folders
        for i in range(len(root)):
            self.unpack_folder(root.recall_entry_i())
        self.section_offsets.append(binfile.names_offset)
        brres.unknown = self.unpack_unknown()
        binfile.end()
        self.post_unpacking(brres)

    def unpack_unknown(self):
        if self.uk_offsets:
            AutoFix.warn('Unknown files {}, may be loosely supported'.format([x[0] for x in self.uk_offsets]))
        uk = []
        for name, offset in self.uk_offsets:
            self.binfile.offset = offset
            uk.append(UnknownUnpacker(self.binfile, self.section_offsets, name).node)
        return uk

    def unpack_subfiles(self, klass, binfile):
        subfolder = Folder(binfile, self.folder_name)
        subfolder.unpack(binfile)
        r = []
        for i in range(len(subfolder)):
            name = subfolder.recall_entry_i()
            self.section_offsets.append(binfile.offset)
            r.append(klass(name, self.node, binfile))
        return r

    def unpack_folder(self, folder_name):
        self.folder_name = folder_name
        if folder_name == "3DModels(NW4R)":
            self.node.models = self.unpack_subfiles(Mdl0, self.binfile)
        elif folder_name == "Textures(NW4R)":
            self.node.textures = self.unpack_subfiles(Tex0, self.binfile)
        elif folder_name == "AnmTexPat(NW4R)":
            self.pat0 = self.unpack_subfiles(Pat0, self.binfile)
        elif folder_name == "AnmTexSrt(NW4R)":
            self.srt0 = self.unpack_subfiles(Srt0, self.binfile)
        elif folder_name == "AnmChr(NW4R)":
            self.node.chr0 = self.unpack_subfiles(Chr0, self.binfile)
        elif folder_name == "AnmScn(NW4R)":
            self.node.scn0 = self.unpack_subfiles(Scn0, self.binfile)
        elif folder_name == "AnmShp(NW4R)":
            self.node.shp0 = self.unpack_subfiles(Shp0, self.binfile)
        elif folder_name == "AnmClr(NW4R)":
            self.node.clr0 = self.unpack_subfiles(Clr0, self.binfile)
        else:
            self.uk_offsets.append((folder_name, self.binfile.offset))
