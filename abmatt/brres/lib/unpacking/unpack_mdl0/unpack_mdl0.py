from brres.lib.binfile import Folder, UnpackingError
from brres.lib.unpacking.interface import Unpacker
from brres.lib.unpacking.unpack_mdl0.unpack_bone import UnpackBone, unpack_bonetable

from brres.lib.unpacking.unpack_mdl0.unpack_color import UnpackColor
from brres.lib.unpacking.unpack_mdl0.unpack_material import UnpackMaterial
from brres.lib.unpacking.unpack_mdl0.unpack_point import UnpackVertex, UnpackUV, UnpackNormal
from brres.lib.unpacking.unpack_mdl0.unpack_polygon import UnpackPolygon
from brres.lib.unpacking.unpack_mdl0.unpack_shader import UnpackShader
from brres.lib.unpacking.unpack_subfile import UnpackSubfile
from brres.mdl0.definition import DrawList, get_definition


class UnpackMdl0(UnpackSubfile):

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
        mdl0.boneTable = unpack_bonetable(binfile, 'I')
        # unpack sections
        self.definitions = self.unpackSection(binfile, self.UnpackDefinition, 'Definitions', return_nodes=False)
        # store bone unpackers to resolve references
        self.bone_unpackers = self.unpackSection(binfile, UnpackBone, 'Bones', return_nodes=False)
        mdl0.vertices = self.unpackSection(binfile, UnpackVertex, 'Vertices')
        mdl0.normals = self.unpackSection(binfile, UnpackNormal, 'Normals')
        mdl0.colors = self.unpackSection(binfile, UnpackColor, 'Colors')
        mdl0.uvs = self.unpackSection(binfile, UnpackUV, 'UVs')
        if mdl0.version >= 10:
            if binfile.recall() or binfile.recall():
                raise UnpackingError(binfile, 'Furs are not supported!')
            # mdl0.fur_vectors = self.unpackSection(binfile, UnpackFurVectors, 'FurVectors')
            # mdl0.fur_layers = self.unpackSection(binfile, UnpackFurLayers, 'FurLayers')
        mdl0.materials = self.unpackSection(binfile, UnpackMaterial, 'Materials')
        mdl0.shaders = self.unpackSection(binfile, UnpackShader, 'Shaders')
        self.poly_unpackers = self.unpackSection(binfile, UnpackPolygon, 'Objects', return_nodes=False)
        self.texture_links = self.unpackSection(binfile, self.UnpackTexLink, 'Textures', return_nodes=False)
        if binfile.recall():
            raise UnpackingError(binfile, 'Palettes are not supported!')
        binfile.end()  # end file
        self.post_unpack(mdl0)

    class UnpackTexLink(Unpacker):
        def __init__(self, name, parent, binfile):
            self.name = name
            super().__init__(parent, binfile)

        def unpack(self, node, binfile):
            self.offset = binfile.start()
            num_references = binfile.read("I", 4)
            self.links = [binfile.read("2i", 8) for i in range(num_references)]
            binfile.end()

    class UnpackDefinition(Unpacker):
        def __init__(self, name, parent, binfile):
            self.name = name
            super().__init__(parent, binfile)

        def unpack(self, mdl0, binfile):
            definition = get_definition(self.name, mdl0, binfile)
            if 'Draw' not in self.name:
                mdl0.__setattr__(self.name, definition)
                self.definition = None
            else:
                self.definition = definition

    def __init__(self, node, binfile):
        self.definitions = []
        self.texture_links = []
        super(UnpackMdl0, self).__init__(node, binfile)

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
        mdl0.bones = [x.node for x in self.bone_unpackers]
        mdl0.objects = [x.node for x in self.poly_unpackers]
        for x in self.bone_unpackers:
            x.post_unpack(self.bone_unpackers)
        for x in self.definitions:
            if x.definition is not None:
                self.parse_definition_list(x.definition.list)
        for x in self.poly_unpackers:
            x.post_unpack()

    def unpackSection(self, binfile, section_klass, name, return_nodes=True):
        """ unpacks section by creating items  of type section_klass
            and adding them to section list index
        """
        # ignore fur sections for v8 mdl0s
        group = []
        # if section_index == 0:
        #     self.unpackDefinitions(mdl0, binfile)
        # elif section_index == 9:
        #     # assumes materials are unpacked..
        #     mdl0.shaders.unpack(binfile, mdl0.materials)
        if binfile.recall():  # from offset header
            # section_klass = mdl0.SECTION_CLASSES[section_index]
            folder = Folder(binfile, name)
            folder.unpack(binfile)
            # section = mdl0.sections[section_index]
            while len(folder.entries):
                name = folder.recallEntryI()
                k = section_klass(name, self.node, binfile=binfile)
                group.append(k) if not return_nodes else group.append(k.node)
        return group

