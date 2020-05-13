#!/usr/bin/Python
#---------------------------------------------------------------------
#   Robert Nelson
#  Structure for working with materials
#---------------------------------------------------------------------


class Material:
    CULL_NONE = 0
    CULL_OUTSIDE = 1
    CULL_INSIDE = 2
    CULL_ALL = 3
    def __init__(self, name):
        self.name = name
        self.alphafunction = 0
        self.blendmode = 0
        self.constantAlpha = 0
        self.layers = []
        self.lightChannels = []
        self.xlu = False
        self.cullmode = self.CULL_INSIDE
        self.shader = 0
        self.shaderColors = 0
        self.shaderConstantColors = 0
        self.compareBeforeTexture = True
        self.enableDepthTest = True
        self.enableDepthUpdate = True
        self.depthFunction = "LessOrEqual"
        self.lightset = 0xff
        self.fogset = 0

    def addTexRef(self, texRef):
        self.layers.append(texRef)

    def getLayer(self, i):
        if i < len(self.layers):
            return self.layers[i]
        return None

    def setTransparent(self):
        # self.alphafunction.enable()
        self.compareBeforeTexture = False
        self.xlu = True

    def setOpaque(self):
        # self.alphafunction.disable() # todo
        self.compareBeforeTexture = True
        self.xlu = False

    def setShader(self, shader):
        self.shader = shader


class TexRef:
    WRAP=["Clamp", "Repeat", "Mirror"]
    FILTER = ["Nearest", "Linear", "Nearest_Mipmap_Nearest", "Linear_Mipmap_Nearest", "Nearest_Mipmap_Linear", "Linear_Mipmap_Linear"]
    ANISOTROPHY = ["One", "Two", "Four"]
    def __init__(self, name):
        self.name = name    # reference to texture
        self.scale = [1, 1]
        self.rotation = 0
        self.translation = [0, 0]
        self.mapmode = 0 # tex coord
        self.uwrap = "Repeat"
        self.vwrap = "Repeat"
        self.minFilter = "Linear_Mipmap_Linear"
        self.magFilter = "Linear"
        self.LODBias = 0.0
        self.maxAnisotrophy = self.ANISOTROPHY[0]
        self.clampBias = True
        self.texelInterpolate = True
        self.projection = "ST"
        self.inputForm = "AB11"
        self.type = "Regular"
        self.coordinates = "TexCoord0"
        self.embossSource = 5
        self.embossLight = 0
        self.normalize = False


class Shader:
    def __init__(self, id):
        self.id = id
        self.stages = [ShaderStage()]

class ShaderStage:
    def __init__(self):
        self.textureMap = 0
        self.textureCoord = 0
        self.textureSwap = 0
        self.rasterColor = "LightChannel0"
        self.rasterSwap = 0
        self.colorConstant = "ConstantColor0"
        self.colorA = 0
        self.colorB = "TextureColor"
        self.colorC = "RasterColor"
        self.colorD = 0
        self.colorBias = 0
        self.colorOperation = "Add"
        self.colorClamp = True
        self.colorScale = "MultiplyBy2"
        self.colorDestination = "OutputColor"
        self.alphaConstant = "ConstantAlpha0"
        self.alphaA = 0
        self.alphaB = "TextureAlpha"
        self.alphaC = "RasterAlpha"
        self.alphaD = 0
        self.alphaBias = 0
        self.alphaOperation = "Add"
        self.alphaClamp = True
        self.alphaScale = "MultiplyBy1"
        self.alphaDestination = "OutputAlpha"
        self.indirectTextureMap = 0xff
        self.indirectTextureCoord = 0xff
        self.indirectBias = 0
        self.indirectMatrix = 0

# LIGHT CHANNEL ----------------------------------------------------
        # LC flags bits
        # 0	Material color enabled
        # 1	Material alpha enabled
        # 2	Ambient color enabled
        # 3	Ambient alpha enabled
        # 4	Raster color enabled
        # 5	Raster alpha enabled
# Light Controls
#   3rd byte 7 for activated, 4th 0-1 for ambient or vertex color
class LightChannel:
    def __init__(self):
        self.flags = 0xff
        self.materialColor = []
        self.ambientColor = []

class BlendMode:
    def __init__(self, enabled):
        self.enabled = enabled
        self.enableBlendLogic = False
        self.srcFactor = "SourceAlpha"
        self.blendLogicOp = "Copy"
        self.dstFactor = "InverseSourceAlpha"
        self.subtract = False


class AlphaFunction:
    def __init__(self, enabled):
        self.ref0 = 128
        self.ref1 = 255
        if enabled:
            self.enable()
        else:
            self.disable()

    def enable(self):
        self.comp0 = ">="
        self.logic = "And"
        self.comp1 = "<="

    def disable(self):
        self.comp0 = "1"
        self.logic = "And"
        self.comp1 = "1"
