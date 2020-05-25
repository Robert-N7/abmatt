''' Layer class '''
from matching import *

def validBool(str):
    if str == "false" or not str or str == "0" or str == "disable":
        return False
    elif str == "true" or str == "1" or str == "enable":
        return True
    raise ValueError("Not a boolean '" + str + "', expected true|false")

# finds index of item, if it is equal to compare index returns -1
# raises error if not found
def indexListItem(list, item, compareIndex):
    for i in range(len(list)):
        if list[i] == item:
            if i != compareIndex:
                return i
            else:
                return -1
    raise ValueError("Invalid setting '" + item + "', Options are: " + str(list))

def parseValStr(value):
    if value[0] == "(" and value[-1] == ")":
        value = value[1:-1]
    return value.split(",")


class Layer:
# ----------------------------------------------------------------------------
#   Constants
# ----------------------------------------------------------------------------
    NUM_SETTINGS = 21
    SETTINGS = (
    "scale", "rotation", "translation", "scn0cameraref",
    "scn0lightref", "mapmode", "uwrap", "vwrap",
    "minfilter", "magfilter", "lodbias", "anisotrophy",
    "clampbias", "texelinterpolate", "projection", "inputform",
    "type", "coordinates", "embosssource", "embosslight",
    "normalize")
    WRAP=("clamp", "repeat", "mirror")
    FILTER = ("nearest", "linear", "nearest_mipmap_nearest", "linear_mipmap_nearest", "nearest_mipmap_linear", "linear_mipmap_linear")
    ANISOTROPHY = ("one", "two", "four")
    MAPMODE = ("texcoord", "envcamera", "projection", "envlight", "envspec")
    PROJECTION = ("st", "stq")
    INPUTFORM = ("ab11", "abc1")
    TYPE = ("regular", "embossmap", "color0", "color1")
    COORDINATES = ("geometry", "normals", "colors", "binfileormalst", "binfileormalsb",
    "texcoord0", "texcoord1", "texcoord2", "texcoord3", "texcoord4", "texcoord5", "texcoord6", "texcoord7")

    def __init__(self, id, name, parent):
        ''' Initializes id (position of layer), name, and parent material '''
        self.id = id
        self.parent = parent
        self.name = name

    def __str__(self):
        return "Layer {}: scale {} rot {} trans {} uwrap {} vwrap {} minfilter {}".format(self.name,
        self.scale, self.rotation, self.translation, self.uwrap, self.vwrap, self.minFilter)

    # ----------------------------------------------------------------------------------
    #   GETTERS
    # ----------------------------------------------------------------------------------
    def getKey(self, key):
        for i in range(self.NUM_SETTINGS):
            if self.SETTINGS[i] == key:
                func = self.GET_SETTINGS[i]
                return func(self)

    def getScale(self):
        return self.scale
    def getRotation(self):
        return self.rotation
    def getTranslation(self):
        return self.translation
    def getScn0LightRef(self):
        return self.scn0LightRef
    def getScn0CameraRef(self):
        return self.scn0CameraRef
    def getMapmode(self):
        return self.MAPMODE[self.mapMode]
    def getUwrap(self):
        return self.WRAP[self.uwrap]
    def getVwrap(self):
        return self.WRAP[self.vwrap]
    def getMinfilter(self):
        return self.FILTER[self.minFilter]
    def getMagfilter(self):
        return self.FILTER[self.magFilter]
    def getLodbias(self):
        return self.LODBias
    def getAnisotrophy(self):
        return self.ANISOTROPHY[self.maxAnisotrophy]
    def getClampbias(self):
        return self.clampBias
    def getTexelInterpolate(self):
        return self.texelInterpolate
    def getProjection(self):
        return self.PROJECTION[self.projection]
    def getInputform(self):
        return self.INPUTFORM[self.inputform]
    def getType(self):
        return self.TYPE[self.type]
    def getCoordinates(self):
        return self.COORDINATES[self.coordinates]
    def getEmbossLight(self):
        return self.embossLight
    def getEmbossSource(self):
        return self.embossSource
    def getNormalize(self):
        return self.normalize

    def getFlagNibble(self):
        return self.enable | self.scaleDefault << 1 \
            | self.rotationDefault << 2 | self.translationDefault << 3

    GET_SETTINGS = ( getScale, getRotation, getTranslation, getScn0CameraRef,
    getScn0LightRef, getMapmode, getUwrap, getVwrap, getMinfilter, getMagfilter,
    getLodbias, getAnisotrophy, getClampbias, getTexelInterpolate, getProjection,
    getInputform, getType, getCoordinates, getEmbossSource, getEmbossLight,
    getNormalize )

    def getSetter(self, key):
        for i in range(self.NUM_SETTINGS):
            if self.SETTINGS[i] == key:
                return self.SET_SETTING[i]

# ----------------------------------------------------------------------------------
#   SETTERS
# ----------------------------------------------------------------------------------

    def setKey(self, key, strValue):
        fun = self.getSetter( key)
        return self.fun(strValue)

    def setScaleStr(self, str):
        values = parseValStr(str)
        if len(values) < 2:
            raise ValueError("Scale requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.scale[0] != i1 or self.scale[1] != i2:
            if i1 != 1 or i2 != 1:
                self.scaleFixed = 0
            else:
                self.scaleFixed = 1
            self.scale = (i1, i2)
            self.isModified = True

    def setRotationStr(self, str):
        f = float(str)
        if f != self.rotation:
            self.rotation = f
            self.rotationFixed = 0 if self.rotation == 0 else 1
            self.isModified = True

    def setTranslationStr(self, str):
        values = parseValStr(str)
        if len(values) < 2:
            raise ValueError("Translation requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.translation[0] != i1 or self.translation[1] != i2:
            self.translation = (i1, i2)
            self.translationFixed = 1 if i1 == 1 and i2 == 1 else 0
            self.isModified = True

    def setCameraRefStr(self, str):
        i = int(str)
        if i != -1 and i != 0:
            raise ValueError("Expected -1 or 0 for camera reference")
        if self.scn0CameraRef != i:
            self.scn0CameraRef = i
            self.isModified = True

    def setLightRefStr(self, str):
        i = int(str)
        if i != -1:
            raise ValueError("Expected -1 for light reference")
        if self.scn0LightRef != i:
            self.scn0LightRef = i
            self.isModified = True

    def setMapmodeStr(self, str):
        i = indexListItem(self.MAPMODE, str, self.mapMode)
        if i >= 0:
            self.mapMode = i
            self.isModified = True

    def setUWrapStr(self, str):
        i = indexListItem(self.WRAP, str, self.uwrap)
        if i >= 0:
            self.uwrap = i
            self.isModified = True

    def setVWrapStr(self, str):
        i = indexListItem(self.WRAP, str, self.vrap)
        if i >= 0:
            self.vrap = i
            self.isModified = True

    def setMinFilterStr(self, str):
        i = indexListItem(self.FILTER, str, self.minFilter)
        if i >= 0:
            self.minFilter = i
            self.isModified = True

    def setMagFilterStr(self, str):
        i = indexListItem(self.FILTER, str, self.magFilter)
        if i > 1:
            raise ValueError("MagFilter out of range (0-1)")
        elif i >= 0:
            self.minFilter = i
            self.isModified = True

    def setLodBiasStr(self, str):
        f = float(str)
        if f != self.LODBias:
            self.LODBias = f
            self.isModified = True

    def setAnisotrophyStr(self, str):
        invalidI = False
        try:
            i = int(str)
            if i != 1 and i != 2 and i != 4:
                invalidI = True
            else:
                i -= 1
                if i > 2:
                    i = 2
        except ValueError:
            i = indexListItem(ANISOTROPHY, str, self.maxAnisotrophy)
        if invalidI:
            raise ValueError("Invalid: '" + str + "', Anisotrophy expects 1|2|4")
        if i >= 0 and i != self.maxAnisotrophy:
            self.maxAnisotrophy = i
            self.isModified = True

    def setClampBiasStr(self, str):
        val = validBool(str)
        if val != self.clampBias:
            self.clampBias = val
            self.isModified = True

    def setTexelInterpolateStr(self, str):
        val = validBool(str)
        if val != self.texelInterpolate:
            self.texelInterpolate = val
            self.isModified = True

    def setProjectionStr(self, str):
        i = indexListItem(self.PROJECTION, str, self.projection)
        if i >= 0:
            self.projection = i
            self.isModified = True

    def setInputFormStr(self, str):
        i = indexListItem(self.INPUTFORM, str, self.inputform)
        if i >= 0:
            self.inputform = i
            self.isModified = True
    def setTypeStr(self, str):
        i = indexListItem(self.TYPE, str, self.type)
        if i >= 0:
            self.type = i
            self.isModified = True

    def setCoordinatesStr(self, str):
        i = indexListItem(self.COORDINATES, str, self.coordinates)
        if i >= 0:
            self.coordinates = i
            self.isModified = True
    def setEmbossSourceStr(self, str):
        i = int(str)
        if not 0 <= i <= 7:
            raise ValueError("Value '" + str + "' out of range for emboss source")
        if self.embossSource != i:
            self.embossSource = i
            self.isModified = True
    def setEmbossLightStr(self, str):
        i = int(str)
        if not 0 <= i <= 255:
            raise ValueError("Value '" + str + "' out of range for emboss light")
        if self.embossLight != i:
            self.embossLight = i
            self.isModified = True
    def setNormalizeStr(self, str):
        val = validBool(str)
        if val != self.normalize:
            self.normalize = val
            self.isModified = True

    def setLayerFlags(self, nibble):
        ''' from lsb, enable, scaledefault, rotationdefault, transdefault '''
        self.enable = nibble & 1
        self.scaleDefault = nibble >> 1 & 1
        self.rotationDefault = nibble >> 2 & 1
        self.translationDefault = nibble >> 3 & 1
        return self.enable

    SET_SETTING = ( setScaleStr, setRotationStr, setTranslationStr, setCameraRefStr,
    setLightRefStr, setMapmodeStr, setUWrapStr, setVWrapStr, setMinFilterStr, setMagFilterStr,
    setLodBiasStr, setAnisotrophyStr, setClampBiasStr, setTexelInterpolateStr, setProjectionStr,
    setInputFormStr, setTypeStr, setCoordinatesStr, setEmbossSourceStr, setEmbossLightStr,
    setNormalizeStr)

# -------------------------------------------------------------------------
# Packing things
# -------------------------------------------------------------------------

    def unpack(self, binfile, scaleOffset):
        ''' unpacks layer information '''
        # assumes material already unpacked name
        binfile.advance(12)
        self.texDataID, self.palleteDataID, self.uwrap, self.vwrap, \
            self.minFilter, self.magFilter, self.LODBias, self.maxAnisotrophy, \
            self.clampBias, self.texelInterpolate, pad = binfile.read("6IfI2BH", 48)
        transforms = binfile.readOffset("5f", scaleOffset)
        self.scale = transforms[0:2]
        self.rotation = transforms[2]
        self.translation = transforms[3:]
        self.scn0CameraRef, self.scn0LightRef, self.mapMode, \
            self.enableIdentityMatrix = binfile.readOffset("4B", scaleOffset + 160)
        self.texMatrix = binfile.readOffset("12f", scaleOffset + 164)

    def pack(self, binfile):
        binfile.advance(12)
        binfile.write("10IfI4BH", self.texDataID, self.palleteDataID,
            self.uwrap, self.vwrap, self.minFilter, self.getMagfilter,
            self.LODBias, self.maxAnisotrophy, self.clampBias,
            self.texelInterpolate, 0)

    def pack_texRef(self, file):
        pack_into("> 10I f I 2B", file.file, file.offset, self.nameOffset, self.palettenameOffset,
        self.textureDataOffset, self.palleteOffset, self.texDataID, self.palleteDataID,
        self.uwrap, self.vwrap, self.minFilter, self.magFilter, self.LODBias, self.maxAnisotrophy,
        self.clampBias, self.texelInterpolate)

    def pack_xfFlags(self, file): # aka texture matrices
        pack_into("> 4B", file.file, file.offset, self.embossLight >> 8, self.embossLight >> 1,
        self.embossLight << 7 & 0x80 | self.embossSource << 4 & 0x70 | self.coordinates >> 1 & 7,
        (self.coordinates & 1) << 7 | (self.projection & 1) << 1 | (self.inputform & 1) << 2 | (self.type & 3) << 4)
        pack_into("> B", file.file, file.offset + 11, self.normalize)

    def info(self, command, trace):
        trace += "->" + self.name
        if matches(command.name, self.name):
            if command.key:
                val = self.getKey(command.key)
                if val:
                    print("{}\t{}:{}".format(trace, command.key, val))
            else:
                print("{}:\tScale:{} Rot:{} Trans:{} UWrap:{} VWrap:{} MinFilter:{} map:{} coord: {}".format(trace,
                self.scale, self.rotation, self.translation,
                self.WRAP[self.uwrap], self.WRAP[self.vwrap], self.FILTER[self.minFilter],
                self.MAPMODE[self.mapMode], self.COORDINATES[self.coordinates]))
