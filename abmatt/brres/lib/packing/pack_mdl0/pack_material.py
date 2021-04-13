from abmatt.brres.lib.packing.interface import Packer
from abmatt.brres.lib.packing.pack_mdl0 import bp, xf


class PackLayer:
    def __init__(self, layer, index):
        self.index = index
        self.layer = layer

    def getFlagNibble(self):
        layer = self.layer
        scale_default = layer.scale[0] == 1 and layer.scale[1] == 1
        rotation_default = layer.rotation == 0
        translation_default = layer.translation[0] == 0 and layer.translation[1] == 0
        return layer.enable | scale_default << 1 \
               | rotation_default << 2 | translation_default << 3

    def pack(self, binfile):
        layer = self.layer
        binfile.start()
        binfile.storeNameRef(layer.name)
        binfile.advance(12)  # ignoring pallete name / offsets
        binfile.write("6IfI2BH", self.index, self.index,
                      layer.uwrap, layer.vwrap, layer.minfilter, layer.magfilter,
                      layer.lod_bias, layer.max_anisotrophy, layer.clamp_bias,
                      layer.texel_interpolate, 0)
        binfile.end()

    def pack_srt(self, binfile):
        """ packs scale rotation translation data """
        layer = self.layer
        binfile.write("5f", layer.scale[0], layer.scale[1], layer.rotation, layer.translation[0], layer.translation[1])


    @staticmethod
    def pack_default_srt(binfile, ntimes):
        for i in range(ntimes):
            binfile.write('5f', 1, 1, 0, 0, 0)

    def pack_textureMatrix(self, binfile):
        """ packs texture matrix """
        layer = self.layer
        binfile.write("4b12f", layer.scn0_camera_ref, layer.scn0_light_ref, layer.map_mode,
                      layer.enable_identity_matrix, *layer.texture_matrix)

    @staticmethod
    def pack_default_textureMatrix(binfile, ntimes):
        for i in range(ntimes):
            binfile.write("4B12f", 0xff, 0xff, 0, 1,
                          1, 0, 0, 0,
                          0, 1, 0, 0,
                          0, 0, 1, 0)

    def pack_xf(self, binfile):
        layer = self.layer
        xf.pack_tex_matrix(binfile, self.index,
                           layer.projection, layer.inputform, layer.type, layer.coordinates,
                           layer.emboss_source, layer.emboss_light)
        xf.pack_dual_tex(binfile, self.index, self.layer.normalize)


class PackMaterial(Packer):
    def create_shader_ref(self, binfile):
        binfile.createRefFrom(self.offset)

    class PackLightChannel(Packer):
        def flagsToInt(self, lc):
            return lc.materialColorEnabled | lc.materialAlphaEnabled << 1 | lc.ambientColorEnabled << 2 \
                   | lc.ambientAlphaEnabled << 3 | lc.rasterColorEnabled << 4 | lc.rasterAlphaEnabled << 5

        def getFlagsAsInt(self, light_control):
            return light_control.materialSourceVertex | light_control.enabled << 1 | light_control.light0123 << 2 | light_control.ambientSourceVertex << 6 \
                   | light_control.diffuseFunction << 7 | light_control.attenuationEnabled << 9 | light_control.attenuationFunction << 10 \
                   | light_control.light4567

        def pack(self, light, binfile):
            flags = self.flagsToInt(light)
            mc = light.materialColor
            binfile.write('I4B', flags, mc[0], mc[1], mc[2], mc[3])
            ac = light.ambientColor
            binfile.write('4B2I', ac[0], ac[1], ac[2], ac[3],
                          self.getFlagsAsInt(light.colorLightControl),
                          self.getFlagsAsInt(light.alphaLightControl))

        @staticmethod
        def pack_default(binfile):
            binfile.write('5I', 0xf, 0xff, 0, 0, 0)

    def __init__(self, node, binfile, index, texture_link_map):
        """
        :type node: Material
        """
        self.texture_link_map = texture_link_map
        self.index = index
        layers = node.layers
        self.layer_packers = [PackLayer(layers[i], i) for i in range(len(layers))]
        super().__init__(node, binfile)

    def pack(self, material, binfile):
        """ Packs the material """
        self.offset = binfile.start()
        binfile.markLen()
        binfile.write("i", binfile.getOuterOffset())
        binfile.storeNameRef(material.name)
        binfile.write("2I4BI3b", self.index, material.xlu << 31, len(material.layers), len(material.lightChannels),
                      material.shaderStages, material.indirectStages, material.cullmode,
                      material.compareBeforeTexture, material.lightset, material.fogset)
        binfile.write("BI4B", 0, 0, 0xff, 0xff, 0xff, 0xff)  # padding, indirect method, light normal map
        binfile.mark()  # shader offset, to be filled
        binfile.write("I", len(material.layers))
        binfile.mark()  # layer offset
        binfile.write("I", 0)  # fur not supported
        if material.parent.version >= 10:
            binfile.advance(4)
            binfile.mark()  # matgx
        else:
            binfile.mark()  # matgx
            binfile.advance(4)
        # ignore precompiled code space
        binfile.advance(360)
        self.pack_layers(binfile)
        binfile.end()

    def pack_layers(self, binfile):
        # layer flags
        x = layerI = bitshift = 0
        layers = self.layer_packers
        empty_layer_count = 8 - len(layers)
        while layerI < len(layers):
            x |= layers[layerI].getFlagNibble() << bitshift
            layerI += 1
            bitshift += 4
        material = self.node
        binfile.write("2I", x, material.textureMatrixMode)
        for l in layers:
            l.pack_srt(binfile)
        # fill in defaults
        PackLayer.pack_default_srt(binfile, empty_layer_count)
        for l in layers:
            l.pack_textureMatrix(binfile)
        PackLayer.pack_default_textureMatrix(binfile, empty_layer_count)
        channels = material.lightChannels
        for i in range(2):
            if i < len(channels):
                self.PackLightChannel(channels[i], binfile)
            else:
                self.PackLightChannel.pack_default(binfile)
        binfile.createRef(1)
        for l in layers:
            # Write Texture linker offsets
            start_offset = self.texture_link_map[l.layer.name].offset
            tex_link_offsets = binfile.references[start_offset]
            binfile.writeOffset('i', tex_link_offsets.pop(0), self.offset - start_offset)  # material offset
            binfile.writeOffset('i', tex_link_offsets.pop(0), binfile.offset - start_offset)  # layer offset
            l.pack(binfile)

        binfile.alignToParent()
        binfile.createRef(1)
        binfile.start()  # MatGX section
        self.pack_mat_gx(binfile)
        offset = binfile.offset
        for l in layers:
            l.pack_xf(binfile)
        binfile.advance(0xa0 - (binfile.offset - offset))
        binfile.end()

    def pack_mat_gx(self, binfile):
        mat = self.node
        bp.pack_alpha_function(binfile, mat.ref0, mat.ref1, mat.comp0, mat.comp1, mat.logic)
        bp.pack_zmode(binfile, mat.depth_test, mat.depth_update, mat.depth_function)
        bp.pack_bp_mask(binfile, 0xffe3)
        bp.pack_blend_mode(binfile, mat.blend_enabled, mat.blend_logic_enabled, mat.blend_dither,
                           mat.blend_update_color, mat.blend_update_alpha, mat.blend_subtract, mat.blend_logic,
                           mat.blend_source, mat.blend_dest)
        bp.pack_constant_alpha(binfile, mat.constant_alpha_enabled, mat.constant_alpha)
        binfile.advance(7)  # pad
        c = mat.colors
        for i in range(len(c)):
            bp.pack_color(binfile, i + 1, c[i], False)
        binfile.advance(4)  # pad
        c = mat.constant_colors
        for i in range(len(c)):
            bp.pack_color(binfile, i, c[i], True)
        binfile.advance(24)

        for i in range(len(mat.ras1_ss)):
            bp.pack_ras1_ss(binfile, mat.ras1_ss[i], i)
        mtx = mat.indirect_matrices
        for i in range(len(mtx)):
            bp.PackIndMtx(mtx[i], binfile, i)
        binfile.advance(9)
