import string

from abmatt.brres.chr0 import Chr0
from abmatt.brres.lib.binfile import Folder
from abmatt.brres.lib.packing.interface import Packer
from abmatt.brres.lib.packing.pack_unknown import UnknownPacker
from abmatt.brres.lib.unpacking.unpack_unknown import UnknownFolder
from abmatt.brres.pat0.pat0 import Pat0
from abmatt.brres.srt0.srt0 import Srt0


class PackBrres(Packer):

    def add_or_create_anim(self, anim, anims, klass, name_map_count):
        for x in anims:
            if self.respect_naming:
                if x.name == anim.get_anim_base_name() and x.add(anim):
                    return True
            elif x.add(anim):
                return True
        count = name_map_count.get(anim.get_anim_base_name())
        name = anim.parent_base_name if not count else anim.parent_base_name + str(count)
        k = klass(name, self.node, base_name=anim.parent_base_name)
        name_map_count[anim.parent_base_name] = count + 1 if count else 1
        k.add(anim)
        anims.append(k)
        return False

    def get_anims(self, unused_anims, model_attr, anim_attr, klass):
        name_map_count = {}
        anims = []
        if unused_anims:
            for x in unused_anims:
                self.add_or_create_anim(x, anims, klass, name_map_count)
        for model in self.node.models:
            for item in getattr(model, model_attr):
                anim = getattr(item, anim_attr)
                if anim:
                    self.add_or_create_anim(anim, anims, klass, name_map_count)
        return anims

    def pre_packing(self, brres):
        self.respect_naming = brres.respect_model_names()
        self.srt0 = self.get_anims(brres.unused_srt0, 'materials', 'srt0', Srt0)
        self.pat0 = self.get_anims(brres.unused_pat0, 'materials', 'pat0', Pat0)
        ret = []
        if brres.models:
            ret.append(('3DModels(NW4R)', brres.models))
        if brres.textures:
            ret.append(('Textures(NW4R)', brres.textures))
        if self.pat0:
            ret.append(('AnmTexPat(NW4R)', self.pat0))
        if self.srt0:
            ret.append(('AnmTexSrt(NW4R)', self.srt0))
        if brres.chr0:
            ret.append(('AnmChr(NW4R)', brres.chr0))
        if brres.scn0:
            ret.append(('AnmScn(NW4R)', brres.scn0))
        if brres.shp0:
            ret.append(('AnmShp(NW4R)', brres.shp0))
        if brres.clr0:
            ret.append(('AnmClr(NW4R)', brres.clr0))
        return ret

    def recursive_add_unknown(self, parent_dir, node):
        parent_dir.addEntry(node.name)
        if type(node) == UnknownFolder:
            f = Folder(self.binfile, node.name)
            node.folder = f
            for x in node.subfiles:
                self.recursive_add_unknown(f, x)
            return f.byteSize()
        return 0

    def generateRoot(self, subfiles):
        """ Generates the root folders
            Does not hook up data pointers,
            returns (rootFolders, bytesize)
        """
        rootFolders = []  # for storing Index Groups
        # Create folder indexing folders
        self.rootFolder = rootFolder = Folder(self.binfile, 'root')
        # Create folder for each section the brres has
        for i in range(len(subfiles)):
            folder_name, folder = subfiles[i]
            size = len(folder)
            if size:
                f = Folder(self.binfile, folder_name)
                for j in range(size):
                    f.addEntry(folder[j].name)  # might not have name?
                rootFolder.addEntry(f.name)
                rootFolders.append(f)
        for uk in self.node.unknown:
            self.recursive_add_unknown(rootFolder, uk)
        return rootFolders

    def __pack_uk_folders_recurse(self, parent_folder, files, first=True):
        if not first:
            parent_folder.pack(self.binfile)
        for f in files:
            if type(f) == UnknownFolder:
                parent_folder.createEntryRef(f.name)
                self.__pack_uk_folders_recurse(f.folder, f.subfiles, False)

    def packRoot(self, binfile, rt_folders):
        """ Packs the root section, returns root folders that need data ptrs"""
        binfile.start()
        binfile.writeMagic("root")
        binfile.markLen()
        self.rootFolder.pack(binfile)
        for f in rt_folders:
            self.rootFolder.createEntryRefI()
            f.pack(binfile)
        self.__pack_uk_folders_recurse(self.rootFolder, self.node.unknown)
        binfile.end()
        binfile.align()
        return rt_folders

    @staticmethod
    def getNumSections(folders):
        """ gets the number of sections, including root"""
        count = 1  # root
        for x in folders:
            if x:
                count += len(x)
                # print('Length of folder {} is {}'.format(x.name, len(x)))
        return count

    def pack(self, brres, binfile):
        """ packs the brres """
        sub_files = self.pre_packing(brres)
        binfile.start()
        rt_folders = self.generateRoot(sub_files)
        binfile.writeMagic(brres.MAGIC)
        binfile.write("H", 0xfeff)  # BOM
        binfile.advance(2)
        binfile.markLen()
        num_sections = self.getNumSections(rt_folders)
        binfile.write("2H", 0x10, num_sections)
        folders = self.packRoot(binfile, rt_folders)
        # now pack the folders
        folder_index = 0
        for name, file_group in sub_files:
            assert len(file_group)
            index_group = folders[folder_index]
            for file in file_group:
                # binfile.section_offsets.append((binfile.offset, file.name))  # - debug
                index_group.createEntryRefI()  # create the dataptr
                file.pack(binfile)
            folder_index += 1
        if brres.unknown:
            self.__recursive_pack_uk(brres.unknown, self.rootFolder)
        binfile.packNames()
        binfile.end()

    def __recursive_pack_uk(self, unknown, parent_folder):
        for i in range(len(unknown)):
            x = unknown[i]
            if type(x) != UnknownFolder:
                parent_folder.createEntryRef(x.name)
                UnknownPacker(x, self.binfile)
            else:
                self.__recursive_pack_uk(x.subfiles, x.folder)
