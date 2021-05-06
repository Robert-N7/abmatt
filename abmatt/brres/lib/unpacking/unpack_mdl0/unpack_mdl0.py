from copy import deepcopy

from abmatt.brres.lib.binfile import Folder, UnpackingError
from abmatt.brres.lib.unpacking.interface import Unpacker
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_bone import UnpackBone, unpack_bonetable
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_color import UnpackColor
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_material import UnpackMaterial
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_point import UnpackVertex, UnpackUV, UnpackNormal
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_polygon import UnpackPolygon
from abmatt.brres.lib.unpacking.unpack_mdl0.unpack_shader import UnpackShader
from abmatt.brres.lib.unpacking.unpack_subfile import UnpackSubfile
from abmatt.brres.mdl0.definition import get_definition


class UnpackMdl0(UnpackSubfile):

    def unpack(self, mdl0, binfile):
        """ unpacks model data """
        super().unpack(mdl0, binfile)
        offset = binfile.start()  # Header
        ln = binfile.readLen()
        fh, mdl0.scaling_rule, mdl0.texture_matrix_mode, mdl0.facepoint_count, \
        mdl0.face_count, _, mdl0.boneCount, _ = binfile.read("i7I", 32)
        binfile.store()  # bone table offset
        if binfile.offset - offset < ln:
            mdl0.minimum = binfile.read("3f", 12)
            mdl0.maximum = binfile.read("3f", 12)
        else:
            mdl0.find_min_max = True
        binfile.end()  # end header
        binfile.recallOffset(offset)
        mdl0.bone_table = unpack_bonetable(binfile, 'i')
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
        self.mat_unpackers = self.unpackSection(binfile, UnpackMaterial, 'Materials', return_nodes=False)
        self.shader_offsets_map = self.unpack_shaders(binfile)
        self.poly_unpackers = self.unpackSection(binfile, UnpackPolygon, 'Objects', return_nodes=False)

        # self.texture_links = self.unpackSection(binfile, self.UnpackTexLink, 'Textures', return_nodes=False)
        if binfile.recall() and binfile.recall():
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
        # self.texture_links = []
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
        # set up mdl0 nodes left
        mdl0.bones = [x.node for x in self.bone_unpackers]
        mdl0.objects = [x.node for x in self.poly_unpackers]
        mdl0.materials = [x.node for x in self.mat_unpackers]
        # hook references
        for x in self.mat_unpackers:
            try:
                shader = self.shader_offsets_map[x.shaderOffset]
            except ValueError:
                raise UnpackingError(self.binfile, 'Material {} shader not found!'.format(x.node.name))
            if shader.parent is not None:   # only use one shader per material
                shader = deepcopy(shader)
            shader.parent = x.node
            x.node.shader = shader
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
        if binfile.recall():  # from offset header
            folder = Folder(binfile, name)
            folder.unpack(binfile)
            while len(folder.entries):
                name = folder.recallEntryI()
                k = section_klass(name, self.node, binfile=binfile)
                group.append(k) if not return_nodes else group.append(k.node)
        return group

    def unpack_shaders(self, binfile):
        # special treatment for shader unpacking, track offsets so as to unpack once only
        shader_offset_map = {}
        if binfile.recall():  # from offset header
            folder = Folder(binfile, 'Shaders')
            folder.unpack(binfile)
            while len(folder.entries):
                name = folder.recallEntryI()
                offset = binfile.offset
                if offset in shader_offset_map:
                    continue
                shader_offset_map[offset] = UnpackShader(name, self.node, binfile=binfile).node
        return shader_offset_map