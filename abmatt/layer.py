""" Layer class """
from copy import copy, deepcopy

from abmatt.matching import parseValStr, indexListItem, validBool, Clipable

from abmatt.wiigraphics.xf import XFTexMatrix, XFDualTex


class Layer(Clipable):
    # ----------------------------------------------------------------------------
    #   Constants
    # ----------------------------------------------------------------------------
    SETTINGS = (
        "scale", "rotation", "translation", "scn0cameraref",
        "scn0lightref", "mapmode", "uwrap", "vwrap",
        "minfilter", "magfilter", "lodbias", "anisotrophy",
        "clampbias", "texelinterpolate", "projection", "inputform",
        "type", "coordinates", "embosssource", "embosslight",
        "normalize", "name")
    WRAP = ("clamp", "repeat", "mirror")
    FILTER = ("nearest", "linear", "nearestmipmapnearest", "linearmipmapnearest", "nearestmipmaplinear",
              "linearmipmaplinear")
    ANISOTROPHY = ("one", "two", "four")
    MAPMODE = ("texcoord", "envcamera", "projection", "envlight", "envspec")
    PROJECTION = ("st", "stq")
    INPUTFORM = ("ab11", "abc1")
    TYPE = ("regular", "embossmap", "color0", "color1")
    COORDINATES = ("geometry", "normals", "colors", "binfileormalst", "binfileormalsb",
                   "texcoord0", "texcoord1", "texcoord2", "texcoord3", "texcoord4", "texcoord5", "texcoord6",
                   "texcoord7")

    def __init__(self, id, name, parent):
        """ Initializes, id (position of layer), name, and parent material """
        self.id = id
        self.parent = parent
        self.name = name
        self.enable = True
        self.scaleDefault = self.rotationDefault = self.translationDefault = True
        self.scale = (1, 1)
        self.rotation = 0
        self.translation = (0, 0)
        self.scn0LightRef = self.scn0CameraRef = -1
        self.mapMode = 0
        self.vwrap = self.uwrap = 1
        self.minfilter = 1
        self.magfilter = 1
        self.LODBias = 0
        self.maxAnisotrophy = 0
        self.texelInterpolate = self.clampBias = False
        self.xfTexMatrix = XFTexMatrix(id)
        self.xfDualTex = XFDualTex(id)
        self.enableIdentityMatrix = True
        self.texMatrix = [1.0, 0, 0, 0,
                          0, 1.0, 0, 0,
                          0, 0, 1.0, 0]

    def __value__(self):
        return "Layer {}: scale {} rot {} trans {} uwrap {} vwrap {} minfilter {}".format(self.name,
                                                                                          self.scale, self.rotation,
                                                                                          self.translation, self.uwrap,
                                                                                          self.vwrap, self.minfilter)

    # ----------------------------------------------------------------------------------
    #   GETTERS
    # ----------------------------------------------------------------------------------
    def __getitem__(self, item):
        for i in range(len(self.SETTINGS)):
            if self.SETTINGS[i] == item:
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
        return self.FILTER[self.minfilter]

    def getMagfilter(self):
        return self.FILTER[self.magfilter]

    def getLodbias(self):
        return self.LODBias

    def getAnisotrophy(self):
        return self.ANISOTROPHY[self.maxAnisotrophy]

    def getClampbias(self):
        return self.clampBias

    def getTexelInterpolate(self):
        return self.texelInterpolate

    def getProjection(self):
        return self.PROJECTION[self.xfTexMatrix["projection"]]

    def getInputform(self):
        return self.INPUTFORM[self.xfTexMatrix["inputform"]]

    def getType(self):
        return self.TYPE[self.xfTexMatrix["type"]]

    def getCoordinates(self):
        return self.COORDINATES[self.xfTexMatrix["coordinates"]]

    def getEmbossLight(self):
        return self.xfTexMatrix["embosslight"]

    def getEmbossSource(self):
        return self.xfTexMatrix["embosssource"]

    def getNormalize(self):
        return self.xfDualTex.normalize

    def getFlagNibble(self):
        return self.enable | self.scaleDefault << 1 \
               | self.rotationDefault << 2 | self.translationDefault << 3

    def getName(self):
        return self.name

    GET_SETTINGS = (getScale, getRotation, getTranslation, getScn0CameraRef,
                    getScn0LightRef, getMapmode, getUwrap, getVwrap, getMinfilter, getMagfilter,
                    getLodbias, getAnisotrophy, getClampbias, getTexelInterpolate, getProjection,
                    getInputform, getType, getCoordinates, getEmbossSource, getEmbossLight,
                    getNormalize, getName)

    def getSetter(self, key):
        for i in range(len(self.SETTINGS)):
            if self.SETTINGS[i] == key:
                return self.SET_SETTING[i]

    # ----------------------------------------------------------------------------------
    #   SETTERS
    # ----------------------------------------------------------------------------------

    def __setitem__(self, key, value):
        fun = self.getSetter(key)
        return fun(self, value)

    def setScaleStr(self, value):
        values = parseValStr(value)
        if len(values) < 2:
            raise ValueError("Scale requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.scale[0] != i1 or self.scale[1] != i2:
            if i1 != 1 or i2 != 1:
                self.scaleDefault = False
            else:
                self.scaleDefault = True
            self.scale = (i1, i2)

    def setRotationStr(self, value):
        f = float(value)
        if f != self.rotation:
            self.rotation = f
            self.rotationDefault = False if self.rotation == 0 else True

    def setTranslationStr(self, value):
        values = parseValStr(value)
        if len(values) < 2:
            raise ValueError("Translation requires 2 floats")
        i1 = float(values[0])
        i2 = float(values[1])
        if self.translation[0] != i1 or self.translation[1] != i2:
            self.translation = (i1, i2)
            self.translationDefault = 1 if i1 == 1 and i2 == 1 else 0

    def setCameraRefStr(self, value):
        i = int(value)
        if i != -1 and i != 0:
            raise ValueError("Expected -1 or 0 for camera reference")
        if self.scn0CameraRef != i:
            self.scn0CameraRef = i

    def setLightRefStr(self, value):
        i = int(value)
        if i != -1:
            raise ValueError("Expected -1 for light reference")
        if self.scn0LightRef != i:
            self.scn0LightRef = i

    def setMapmodeStr(self, value):
        i = indexListItem(self.MAPMODE, value, self.mapMode)
        if i >= 0:
            self.mapMode = i

    def setUWrapStr(self, value):
        i = indexListItem(self.WRAP, value, self.uwrap)
        if i >= 0:
            self.uwrap = i

    def setVWrapStr(self, value):
        i = indexListItem(self.WRAP, value, self.vwrap)
        if i >= 0:
            self.vwrap = i

    def setMinFilterStr(self, value):
        value = value.replace('_', '')
        i = indexListItem(self.FILTER, value, self.minfilter)
        if i >= 0:
            self.minfilter = i

    def setMagFilterStr(self, value):
        i = indexListItem(self.FILTER, value, self.magfilter)
        if i > 1:
            raise ValueError("MagFilter out of range (0-1)")
        elif i >= 0:
            self.minfilter = i

    def setLodBiasStr(self, value):
        f = float(value)
        if f != self.LODBias:
            self.LODBias = f

    def setAnisotrophyStr(self, value):
        invalidI = False
        try:
            i = int(value)
            if i != 1 and i != 2 and i != 4:
                invalidI = True
            else:
                i -= 1
                if i > 2:
                    i = 2
        except ValueError:
            i = indexListItem(self.ANISOTROPHY, value, self.maxAnisotrophy)
        if invalidI:
            raise ValueError("Invalid: '" + value + "', Anisotrophy expects 1|2|4")
        if i >= 0 and i != self.maxAnisotrophy:
            self.maxAnisotrophy = i

    def setClampBiasStr(self, value):
        val = validBool(value)
        if val != self.clampBias:
            self.clampBias = val

    def setTexelInterpolateStr(self, value):
        val = validBool(value)
        if val != self.texelInterpolate:
            self.texelInterpolate = val

    def setProjectionStr(self, value):
        i = indexListItem(self.PROJECTION, value, self.xfTexMatrix["projection"])
        if i >= 0:
            self.xfTexMatrix["projection"] = i

    def setInputFormStr(self, value):
        i = indexListItem(self.INPUTFORM, value, self.xfTexMatrix["inputform"])
        if i >= 0:
            self.xfTexMatrix["inputform"] = i

    def setTypeStr(self, value):
        i = indexListItem(self.TYPE, value, self.xfTexMatrix["type"])
        if i >= 0:
            self.xfTexMatrix["type"] = i

    def setCoordinatesStr(self, value):
        i = indexListItem(self.COORDINATES, value, self.xfTexMatrix["coordinates"])
        if i >= 0:
            self.xfTexMatrix["coordinates"] = i

    def setEmbossSourceStr(self, value):
        i = int(value)
        if not 0 <= i <= 7:
            raise ValueError("Value '" + value + "' out of range for emboss source")
        if self.xfTexMatrix["embosssource"] != i:
            self.xfTexMatrix["embosssource"] = i

    def setEmbossLightStr(self, value):
        i = int(value)
        if not 0 <= i <= 255:
            raise ValueError("Value '" + value + "' out of range for emboss light")
        if self.xfTexMatrix["embosslight"] != i:
            self.xfTexMatrix["embosslight"] = i

    def setNormalizeStr(self, value):
        val = validBool(value)
        if val != self.xfDualTex.normalize:
            self.xfDualTex.normalize = val

    def setLayerFlags(self, nibble):
        """ from lsb, enable, scaledefault, rotationdefault, transdefault """
        self.enable = nibble & 1
        self.scaleDefault = nibble >> 1 & 1
        self.rotationDefault = nibble >> 2 & 1
        self.translationDefault = nibble >> 3 & 1
        return self.enable

    def setName(self, value):
        self.name = self.parent.renameLayer(self, value)

    SET_SETTING = (setScaleStr, setRotationStr, setTranslationStr, setCameraRefStr,
                   setLightRefStr, setMapmodeStr, setUWrapStr, setVWrapStr, setMinFilterStr, setMagFilterStr,
                   setLodBiasStr, setAnisotrophyStr, setClampBiasStr, setTexelInterpolateStr, setProjectionStr,
                   setInputFormStr, setTypeStr, setCoordinatesStr, setEmbossSourceStr, setEmbossLightStr,
                   setNormalizeStr, setName)

    # -------------------------------------- PASTE ---------------------------
    def paste(self, item):
        if self.name == 'Null':
            self.setName(item.name)
        self.uwrap = item.uwrap
        self.vwrap = item.vwrap
        self.minfilter = item.minfilter
        self.magfilter = item.magfilter
        self.LODBias = item.LODBias
        self.maxAnisotrophy = item.maxAnisotrophy
        self.clampBias = item.clampBias
        self.texelInterpolate = item.texelInterpolate
        self.scale = (item.scale[0], item.scale[1])
        self.rotation = item.rotation
        self.translation = (item.translation[0], item.translation[1])
        self.scn0CameraRef = item.scn0CameraRef
        self.scn0LightRef = item.scn0LightRef
        self.mapMode = item.mapMode
        self.enableIdentityMatrix = item.enableIdentityMatrix
        self.texMatrix = copy(item.texMatrix)
        self.xfTexMatrix = deepcopy(item.xfTexMatrix)
        self.xfDualTex = deepcopy(item.xfDualTex)

    # -------------------------------------------------------------------------
    # Packing things
    # -------------------------------------------------------------------------

    def unpack(self, binfile, scaleOffset):
        """ unpacks layer information """
        # assumes material already unpacked name
        binfile.advance(12)
        texDataID, palleteDataID, self.uwrap, self.vwrap, \
        self.minfilter, self.magfilter, self.LODBias, self.maxAnisotrophy, \
        self.clampBias, self.texelInterpolate, pad = binfile.read("6IfI2BH", 0x24)
        transforms = binfile.readOffset("5f", scaleOffset)
        self.scale = transforms[0:2]
        self.rotation = transforms[2]
        self.translation = transforms[3:]
        # print("Texid {} palleteid {} uwrap {} vwrap {} scale {} rot {} trans{}" \
        #       .format(self.texDataID, self.palleteDataID, self.uwrap, self.vwrap, self.scale, self.rotation,
        #               self.translation))

    def unpack_textureMatrix(self, binfile):
        self.scn0CameraRef, self.scn0LightRef, self.mapMode, \
        self.enableIdentityMatrix = binfile.read("4b", 4)
        self.texMatrix = binfile.read("12f", 48)

    def unpackXF(self, binfile):
        """Unpacks Wii graphics """
        self.xfTexMatrix.unpack(binfile)
        self.xfDualTex.unpack(binfile)

    def pack(self, binfile):
        binfile.start()
        binfile.storeNameRef(self.name)
        binfile.advance(12)  # ignoring pallete name / offsets
        binfile.write("6IfI2BH", self.id, self.id,
                      self.uwrap, self.vwrap, self.minfilter, self.magfilter,
                      self.LODBias, self.maxAnisotrophy, self.clampBias,
                      self.texelInterpolate, 0)
        binfile.end()

    def pack_srt(self, binfile):
        """ packs scale rotation translation data """
        binfile.write("5f", self.scale[0], self.scale[1], self.rotation, self.translation[0], self.translation[1])

    @staticmethod
    def pack_default_srt(binfile, ntimes):
        for i in range(ntimes):
            binfile.write('5f', 1, 1, 0, 0, 0)

    def pack_textureMatrix(self, binfile):
        """ packs texture matrix """
        binfile.write("4b12f", self.scn0CameraRef, self.scn0LightRef, self.mapMode,
                      self.enableIdentityMatrix, *self.texMatrix)

    @staticmethod
    def pack_default_textureMatrix(binfile, ntimes):
        for i in range(ntimes):
            binfile.write("4B12f", 0xff, 0xff, 0, 1,
                          1, 0, 0, 0,
                          0, 1, 0, 0,
                          0, 0, 1, 0)

    def pack_xf(self, binfile):
        self.xfTexMatrix.pack(binfile)
        self.xfDualTex.pack(binfile)

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + self.name if indentation_level else '>' + self.parent.name + "->" + self.name
        if key:
            val = self[key]
            print("{}\t{}:{}".format(trace, key, val))
        else:
            print("{}:\tScale:{} Rot:{} Trans:{} UWrap:{} VWrap:{} MinFilter:{}".format(
                                                         trace, self.scale, self.rotation, self.translation,
                                                         self.WRAP[self.uwrap], self.WRAP[self.vwrap],
                                                         self.FILTER[self.minfilter], self.MAPMODE[self.mapMode]))

    def uses_mipmaps(self):
        return self.minfilter > 1

    def check(self, texture_map, loudness):
        if loudness > 1:
            if self.uses_mipmaps():
                if texture_map[self.name].num_mips == 0:
                    print('CHECK: {} mipmaps enabled but no mipmaps in TEX0.'.format(self.parent.name + '->' + self.name))
            else:
                if texture_map[self.name].num_mips > 0:
                    print('CHECK: {} mipmaps disabled but TEX0 has {}'.format(self.parent.name + '->' + self.name,
                                                                              texture_map[self.name].num_mips))
        self.xfTexMatrix.check()