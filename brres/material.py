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
        self.alphafunction = AlphaFunction(0)
        self.blendmode = BlendMode(0)
        self.constantAlpha = 0
        self.texgens = []
        self.lightChannels = (LightChannel(1), LightChannel(0))
        self.xlu = False
        self.cullmode = self.CULL_INSIDE
        self.shader = 0
        self.shaderColors = [[0,0,0,0], [0,0,0,0], [0,0,0,0]]
        self.shaderConstantColors = [[0,0,0,0], [0,0,0,0], [0,0,0,0], [0,0,0,0]]
        self.compareBeforeTexture = True
        self.enableDepthTest = True
        self.enableDepthUpdate = True
        self.depthFunction = "LessOrEqual"
        self.lightset = 0xff
        self.fogset = 0

    def addTexGen(self, texRef):
        self.texgens.append(texRef)

    def setTransparent(self):
        self.alphafunction.enable()
        self.compareBeforeTexture = False
        self.xlu = True

    def setOpaque(self):
        self.alphafunction.disable()
        self.compareBeforeTexture = True
        self.xlu = False

    def setShader(self, shader):
        self.shader = shader


class TexRef:
    def __init__(self, name):
        self.name = name    # reference to texture
        self.scale = [1, 1]
        self.rotation = 0
        self.translation = [0, 0]
        self.mapmode = "TexCoord"
        self.uwrap = "Repeat"
        self.vwrap = "Repeat"
        self.minFilter = "Linear_Mipmap_Linear"
        self.magFilter = "Linear"
        self.LODBias = 0
        self.maxAnisotrophy = "Four"
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

class LightChannel:
    def __init__(self, enabled):
        self.rasterColorOn = enabled    # disabled in lc2
        self.rasterAlphaOn = enabled    # ditto
        self.ambientColorOn = True
        self.ambientAlphaOn = True
        self.materialColorOn = True
        self.materialAlphaOn = True
        self.materialColor = [0xff, 0xff, 0xff, 0xff]
        self.ambientColor = [0x00, 0x00, 0x00, 0xff]
        self.colorOn = False
        self.alphaOn = False
        if(enabled):
            self.colorMaterialSource = "Vertex"     # this may be changed to register
            self.alphaMaterialSource = "Vertex"
            self.colorDiffuseFunction = "Clamped"
            self.alphaDiffuseFunction = "Clamped"
            self.colorAttenuation = "Spotlight"
            self.alphaAttenuation = "Spotlight"
        else:
            self.colorMaterialSource = "Register"
            self.alphaMaterialSource = "Register"
            self.colorDiffuseFunction = 0
            self.alphaDiffuseFunction = 0
            self.colorAttenuation = 0
            self.alphaAttenuation = 0
        self.colorAmbientSource = "Register"
        self.alphaAmbientSource = "Register"

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
