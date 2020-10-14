from brres.lib.unpacking.interface import Unpacker
from brres.mdl0.layer import Layer


class UnpackMaterial(Unpacker):
    class UnpackLayer(Unpacker):
        pass

    def __init__(self, node, binfile):
        super().__init__(node, binfile)

    def unpackLayers(self, binfile, startLayerInfo, numlayers):
        """ unpacks the material layers """
        material = self.node
        binfile.recall()  # layers
        offset = binfile.offset
        for i in range(numlayers):
            binfile.start()
            scale_offset = startLayerInfo + 8 + i * 20
            layer = Layer(len(material.layers), binfile.unpack_name(), material)

            material.layers.append(layer)
            layer.unpack(binfile, scale_offset)
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
        for layer in material.layers:
            layer.unpack_textureMatrix(binfile)
        return offset

    def unpackLightChannels(self, binfile, nlights):
        """ Unpacks the light channels """
        for i in range(nlights):
            self.node.lightChannels.append(LightChannel(binfile))

    def unpack_matgx(self, mat, binfile):
        pass

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
        if nlayers != ntexgens:
            raise Exception('Number of layers {} is different than number texgens {}'.format(nlayers, ntexgens))
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
        self.unpackLayers(binfile, startlayerInfo, nlayers)
        binfile.offset = startlayerInfo + 584
        self.unpackLightChannels(binfile, nlights)
        binfile.recall()
        binfile.start()  # Mat wii graphics
        self.unpack_matgx(material, binfile)
        for layer in material.layers:
            layer.unpackXF(binfile)
        binfile.end()
        binfile.end()

