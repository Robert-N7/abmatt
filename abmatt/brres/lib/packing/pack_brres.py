from brres.lib.binfile import Folder
from brres.lib.packing.interface import Packer


class PackBrres(Packer):
    def pre_packing(self, brres):
        brres.check()
        folders = brres.folders
        ret = []
        ordered = brres.ORDERED
        anim_collect = brres.ANIM_COLLECTIONS
        added = set()
        for folder in ordered:
            x = folders.get(folder)
            if x:
                ret.append((folder, x))
                added.add(folder)
        for folder in anim_collect:
            x = folders.get(folder)
            if x:
                ret.append((folder, brres.get_anim_for_packing(x)))
                added.add(folder)
        for x in folders:
            if x not in added:
                ret.append((x, folders[x]))
        return ret

    def generateRoot(self, subfiles):
        """ Generates the root folders
            Does not hook up data pointers except the head group,
            returns (rootFolders, bytesize)
        """
        rootFolders = []  # for storing Index Groups
        byteSize = 0
        # Create folder indexing folders
        rootFolder = Folder(self.binfile, self.node.ROOTMAGIC)
        rootFolders.append(rootFolder)
        offsets = []  # for tracking offsets from first group to others
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

    @staticmethod
    def getNumSections(folders):
        """ gets the number of sections, including root"""
        count = 1  # root
        for x in folders[count:]:
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
            if len(file_group):
                index_group = folders[folder_index]
                for file in file_group:
                    index_group.createEntryRefI()  # create the dataptr
                    file.pack(binfile)
                folder_index += 1
        binfile.packNames()
        binfile.end()
