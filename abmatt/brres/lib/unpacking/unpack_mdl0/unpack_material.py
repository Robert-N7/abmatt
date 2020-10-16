from brres.lib.binfile import UnpackingError
from brres.lib.unpacking.interface import Unpacker
from brres.lib.unpacking.unpack_mdl0 import bp
from brres.mdl0.layer import Layer
from brres.mdl0.material.light import LightChannel
from brres.mdl0.material.material import Material
from brres.mdl0.wiigraphics.bp import IndMatrix


class UnpackLayer(Unpacker):
    def __init__(self, node, binfile, scaleOffset, layer_index):
        self.scaleOffset = scaleOffset
        self.layer_index = layer_index
        super().__init__(node, binfile)

    def unpack(self, layer, binfile):
        """ unpacks layer information """
        # assumes material already unpacked name
        binfile.advance(12)
        texDataID, palleteDataID, layer.uwrap, layer.vwrap, \
        layer.minfilter, layer.magfilter, layer.lod_bias, layer.max_anisotrophy, \
        layer.clamp_bias, layer.texel_interpolate, pad = binfile.read("6IfI2BH", 0x24)
        transforms = binfile.readOffset("5f", self.scaleOffset)
        layer.scale = transforms[0:2]
        layer.rotation = transforms[2]
        layer.translation = transforms[3:]
        # print("Texid {} palleteid {} uwrap {} vwrap {} scale {} rot {} trans{}" \
        #       .format(self.texDataID, self.palleteDataID, self.uwrap, self.vwrap, self.scale, self.rotation,
        #               self.translation))

    def unpack_textureMatrix(self):
        layer = self.node
        layer.scn0_camera_ref, layer.scn0_light_ref, layer.map_mode, \
        layer.enable_identity_matrix = self.binfile.read("4b", 4)
        layer.texture_matrix = self.binfile.read("12f", 48)

    def unpack_xf_command(self, binfile):
        enabled, tsize, address = binfile.read("B2H", 5)
        size = tsize + 1
        if not enabled:
            binfile.advance(4)
            return 0
        return binfile.read("{}I".format(size), size * 4)

    def unpack_xf(self, binfile):
        """Unpacks Wii graphics """
        layer = self.node
        [x] = self.unpack_xf_command(binfile)
        if x:
            layer.projection = x >> 1 & 1
            layer.inputform = x >> 2 & 3
            layer.type = x >> 4 & 7
            layer.coordinates = x >> 7 & 0x1f
            layer.enboss_source = x >> 0xc & 7
            layer.emboss_light = x >> 0xf & 0xffff

        [d] = self.unpack_xf_command(binfile)
        if d:
            layer.normalize = d >> 8 & 1


class UnpackLightChannel(Unpacker):
    def unpack(self, lc, binfile):
        data = binfile.read("I8B2I", 20)
        flags = data[0]
        lc.materialColorEnabled = flags & 1
        lc.materialAlphaEnabled = flags >> 1 & 1
        lc.ambientColorEnabled = flags >> 2 & 1
        lc.ambientAlphaEnabled = flags >> 3 & 1
        lc.rasterColorEnabled = flags >> 4 & 1
        lc.rasterAlphaEnabled = flags >> 5 & 1
        lc.materialColor = data[1:5]
        lc.ambientColor = data[5:9]
        lc.colorLightControl = lc.LightChannelControl(data[9])
        lc.alphaLightControl = lc.LightChannelControl(data[10])


class UnpackMaterial(Unpacker):
    def __init__(self, name, node, binfile):
        mat = Material(name, node)
        self.layers = []
        super().__init__(mat, binfile)

    def unpack_layers(self, binfile, startLayerInfo, numlayers):
        """ unpacks the material layers """
        material = self.node
        binfile.recall()  # layers
        offset = binfile.offset
        for i in range(numlayers):
            binfile.start()
            scale_offset = startLayerInfo + 8 + i * 20
            layer = Layer(binfile.unpack_name(), material)
            layer_id = len(material.layers)
            material.layers.append(layer)
            self.layers.append(UnpackLayer(layer, binfile, scale_offset, layer_id))
            binfile.end()
        # Layer Flags
        binfile.offset = startLayerInfo
        flags = binfile.read("4B", 4)
        i = 3
        for li in range(len(material.layers)):
            if li % 2 == 0:
                f = flags[i]
            else:
                f = flags[i] >> 4
                i -= 1
            material.layers[li].setLayerFlags(f)
        [material.textureMatrixMode] = binfile.read('I', 4)
        # Texture matrix
        binfile.advance(160)
        for layer in self.layers:
            layer.unpack_textureMatrix()
        return offset

    def unpack_light_channels(self, binfile, nlights):
        """ Unpacks the light channels """
        for i in range(nlights):
            lc = LightChannel()
            UnpackLightChannel(lc, binfile)
            self.node.lightChannels.append(lc)

    def unpack_shader_color(self, binfile, is_constant):
        red, alpha = bp.unpack_color_reg(binfile)
        green, blue = bp.unpack_color_reg(binfile)
        if is_constant:
            binfile.advance(10)
        return red, green, blue, alpha

    def unpack_matgx(self, mat, binfile):
        mat.ref0, mat.ref1, mat.comp0, mat.comp1, mat.logic = bp.unpack_alpha_function(binfile)
        mat.depth_test, mat.depth_update, mat.depth_function = bp.unpack_zmode(binfile)
        bp.unpack_bp(binfile)   # mask
        bp.unpack_blend_mode(mat, binfile)
        mat.constant_alpha_enabled, mat.constant_alpha = bp.unpack_constant_alpha(binfile)
        binfile.advance(7)  # pad - unknown?
        mat.colors = [self.unpack_shader_color(binfile, False) for i in range(3)]
            # self.tevRegs[i].unpack(binfile)
        binfile.advance(4)  # pad - unknown?
        mat.constant_colors = [self.unpack_shader_color(binfile, True) for i in range(4)]
        # for i in range(len(self.cctevRegs)):
        #     self.cctevRegs[i].unpack(binfile)
        binfile.advance(24)
        mat.ras1 = [bp.unpack_bp(binfile) for i in range(2)]
        mat.indirect_matrices = [bp.UnpackIndMtx(IndMatrix(), binfile).node for i in range(3)]
        binfile.advance(9)


    def unpack(self, material, binfile):
        """ Unpacks material """
        self.offset = binfile.start()
        # print('Material {} offset {}'.format(self.name, offset))
        binfile.readLen()
        binfile.advance(8)
        material.index, xluFlags, ntexgens, nlights, \
        material.shaderStages, material.indirectStages, \
        material.cullmode, material.compareBeforeTexture, \
        material.lightset, material.fogset, pad = binfile.read("2I2B2BI4b", 20)
        material.xlu = xluFlags >> 31 & 1
        assert (xluFlags & 0x7fffffff) == 0
        assert nlights <= 2
        binfile.advance(8)
        self.shaderOffset, nlayers = binfile.read("2i", 8)
        self.shaderOffset += self.offset
        if nlayers != ntexgens:
            raise UnpackingError('Number of layers {} is different than number texgens {}'.format(nlayers, ntexgens))
        material.shaderOffset += binfile.beginOffset
        binfile.store()  # layer offset
        if material.parent.version >= 10:
            binfile.advance(8)
            # bo = binfile.offset
            # [dpo] = binfile.readOffset("I", binfile.offset)
            binfile.store()  # store matgx offset
        else:
            binfile.advance(4)
            binfile.store()  # store matgx offset
            # binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        startlayerInfo = binfile.offset
        # [self.textureMatrixMode] = binfile.readOffset('I', binfile.offset + 4)
        self.unpack_layers(binfile, startlayerInfo, nlayers)
        binfile.offset = startlayerInfo + 584
        self.unpack_light_channels(binfile, nlights)
        binfile.recall()
        binfile.start()  # Mat wii graphics
        self.unpack_matgx(material, binfile)
        for layer in self.layers:
            layer.unpack_xf(binfile)
        binfile.end()
        binfile.end()

