from brres.lib.binfile import Folder
from brres.lib.unpacking.unpack_subfile import UnpackSubfile
from brres.mdl0.bone import BoneTable, Bone
from brres.mdl0.definition import DrawList, get_definition


class UnpackMdl0(UnpackSubfile):
    def parse_definition_list(self, li):
        mdl0 = self.node
        for x in li:
            poly = mdl0.objects[x.objIndex]
            mat = mdl0.materials[x.matIndex]
            bone = mdl0.bones[x.boneIndex]
            poly.material = mat
            mat.polygons.append(poly)
            poly.visible_bone = bone
            poly.priority = x.priority

    def post_unpack(self, mdl0):
        Bone.post_unpack(mdl0.bones)
        if mdl0.DrawOpa:
            self.parse_definition_list(mdl0.DrawOpa.list)
        if mdl0.DrawXlu:
            self.parse_definition_list(mdl0.DrawXlu.list)


    def unpackSection(self, binfile, section_index):
        """ unpacks section by creating items  of type section_klass
            and adding them to section list index
        """
        # ignore fur sections for v8 mdl0s
        mdl0 = self.node
        if section_index == 0:
            self.unpackDefinitions(mdl0, binfile)
        elif section_index == 9:
            # assumes materials are unpacked..
            mdl0.shaders.unpack(binfile, mdl0.materials)
        elif binfile.recall():  # from offset header
            section_klass = mdl0.SECTION_CLASSES[section_index]
            folder = Folder(binfile, mdl0.SECTION_NAMES[section_index])
            folder.unpack(binfile)
            section = mdl0.sections[section_index]
            while len(folder.entries):
                name = folder.recallEntryI()
                section.append(section_klass(name, mdl0, binfile))
            return len(section)

    def unpackDefinitions(self, mdl0, binfile):
        binfile.recall()
        folder = Folder(binfile, mdl0.SECTION_NAMES[0])
        folder.unpack(binfile)
        found_xlu = found_opa = False
        while len(folder.entries):
            name = folder.recallEntryI()
            mdl0.__setattr__(name, get_definition(name, mdl0, binfile))
        if not mdl0.DrawOpa:
            mdl0.DrawOpa = DrawList('DrawOpa', mdl0)
        if not mdl0.DrawXlu:
            mdl0.DrawXlu = DrawList('DrawXlu', mdl0)


    def unpack(self, mdl0, binfile):
        """ unpacks model data """
        super().unpack(mdl0, binfile)
        offset = binfile.start()  # Header
        ln = binfile.readLen()
        fh, mdl0.scaling_rule, mdl0.texture_matrix_mode, mdl0.facepoint_count, \
        mdl0.faceCount, _, mdl0.boneMatrixCount, _ = binfile.read("i7I", 32)
        binfile.store()  # bone table offset
        if binfile.offset - offset < ln:
            mdl0.minimum = binfile.read("3f", 12)
            mdl0.maximum = binfile.read("3f", 12)
        else:
            mdl0.find_min_max = True
        binfile.end()  # end header
        binfile.recallOffset(offset)
        mdl0.boneTable = BoneTable()
        mdl0.boneTable.unpack(binfile)
        # unpack sections
        i = 0
        while i < 14:
            if mdl0.version < 10:
                if i == 6:
                    i += 2
                elif i == 13:
                    break
            mdl0.unpackSection(binfile, i)
            i += 1
        binfile.end()  # end file
        self.post_unpack(mdl0)
