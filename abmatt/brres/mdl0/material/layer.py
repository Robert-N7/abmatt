""" Layer class """
from copy import copy, deepcopy

from abmatt.brres.lib.matching import parseValStr, indexListItem, validBool, fuzzy_strings
from abmatt.brres.lib.node import Clipable

from abmatt.brres.mdl0.wiigraphics.xf import XFTexMatrix, XFDualTex
from autofix import Bug


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
    EXT = 'layr'
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
    MINFILTER_AUTO = False
    RENAME_UNKNOWN_REFS = True
    REMOVE_UNKNOWN_REFS = True

    def __init__(self, name, parent, binfile=None):
        """ Initializes, id (position of layer), name, and parent material """
        self.enable_identity_matrix = True
        self.tex0 = None
        self.projection = 0
        self.inputform = 0
        self.type = 0
        self.coordinates = 5
        self.emboss_source = 5
        self.emboss_light = 0
        self.texture_matrix = [1.0, 0, 0, 0,
                               0, 1.0, 0, 0,
                               0, 0, 1.0, 0]
        super(Layer, self).__init__(name, parent, binfile)

    def begin(self):
        self.enable = True
        self.scale = [1, 1]
        self.rotation = 0
        self.translation = [0, 0]
        self.scn0_light_ref = self.scn0_camera_ref = -1
        self.map_mode = 0
        self.vwrap = self.uwrap = 1
        self.minfilter = 1
        self.magfilter = 1
        self.lod_bias = 0
        self.max_anisotrophy = 0
        self.texel_interpolate = self.clamp_bias = False
        self.normalize = 0

    def __value__(self):
        return "Layer {}: scale {} rot {} trans {} uwrap {} vwrap {} minfilter {}".format(self.name,
                                                                                          self.scale, self.rotation,
                                                                                          self.translation, self.uwrap,
                                                                                          self.vwrap, self.minfilter)

    # ----------------------------------------------------------------------------------
    #   GETTERS
    # ----------------------------------------------------------------------------------
    def get_str(self, item):
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
        return self.scn0_light_ref

    def getScn0CameraRef(self):
        return self.scn0_camera_ref

    def getMapmode(self):
        return self.MAPMODE[self.map_mode]

    def getUwrap(self):
        return self.WRAP[self.uwrap]

    def getVwrap(self):
        return self.WRAP[self.vwrap]

    def getMinfilter(self):
        return self.FILTER[self.minfilter]

    def getMagfilter(self):
        return self.FILTER[self.magfilter]

    def getLodbias(self):
        return self.lod_bias

    def getAnisotrophy(self):
        return self.ANISOTROPHY[self.max_anisotrophy]

    def getClampbias(self):
        return self.clamp_bias

    def getTexelInterpolate(self):
        return self.texel_interpolate

    def getProjection(self):
        return self.PROJECTION[self.projection]

    def getInputform(self):
        return self.INPUTFORM[self.inputform]

    def getType(self):
        return self.TYPE[self.type]

    def getCoordinates(self):
        return self.COORDINATES[self.coordinates]

    def get_uv_channel(self):
        val = self.coordinates - 5
        return val if val >= 0 else None

    def getEmbossLight(self):
        return self.emboss_light

    def getEmbossSource(self):
        return self.emboss_source

    def getNormalize(self):
        return self.normalize

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

    def set_str(self, key, value):
        fun = self.getSetter(key)
        return fun(self, value)

    def set_scale(self, scale):
        if self.scale != scale:
            self.scale = scale
            self.mark_modified()

    def setScaleStr(self, value):
        values = parseValStr(value)
        if len(values) < 2:
            raise ValueError("Scale requires 2 floats")
        self.set_scale((float(values[0]), float(values[1])))

    def set_rotation(self, rotation):
        if self.rotation != rotation:
            self.rotation = rotation
            self.mark_modified()

    def setRotationStr(self, value):
        self.set_rotation(float(value))

    def set_translation(self, translation):
        if self.translation != translation:
            self.translation = translation
            self.mark_modified()

    def setTranslationStr(self, value):
        values = parseValStr(value)
        if len(values) < 2:
            raise ValueError("Translation requires 2 floats")
        self.set_translation((float(values[0]), float(values[1])))

    def setCameraRefStr(self, value):
        i = int(value)
        if i != -1 and i != 0:
            raise ValueError("Expected -1 or 0 for camera reference")
        if self.scn0_camera_ref != i:
            self.scn0_camera_ref = i
            self.mark_modified()

    def setLightRefStr(self, value):
        i = int(value)
        if i != -1:
            raise ValueError("Expected -1 for light reference")
        if self.scn0_light_ref != i:
            self.scn0_light_ref = i
            self.mark_modified()

    def setMapmodeStr(self, value):
        i = indexListItem(self.MAPMODE, value, self.map_mode)
        if i >= 0:
            self.map_mode = i
            self.mark_modified()

    def setUWrapStr(self, value):
        i = indexListItem(self.WRAP, value, self.uwrap)
        if i >= 0:
            self.uwrap = i
            self.mark_modified()

    def setVWrapStr(self, value):
        i = indexListItem(self.WRAP, value, self.vwrap)
        if i >= 0:
            self.vwrap = i
            self.mark_modified()

    def setMinFilterStr(self, value):
        value = value.replace('_', '')
        i = indexListItem(self.FILTER, value, self.minfilter)
        if i >= 0:
            self.minfilter = i
            self.mark_modified()

    def setMagFilterStr(self, value):
        i = indexListItem(self.FILTER, value, self.magfilter)
        if i > 1:
            raise ValueError("MagFilter out of range (0-1)")
        elif i >= 0:
            self.minfilter = i
            self.mark_modified()

    def setLodBiasStr(self, value):
        f = float(value)
        if f != self.lod_bias:
            self.lod_bias = f
            self.mark_modified()

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
            i = indexListItem(self.ANISOTROPHY, value, self.max_anisotrophy)
        if invalidI:
            raise ValueError("Invalid: '" + value + "', Anisotrophy expects 1|2|4")
        if i >= 0 and i != self.max_anisotrophy:
            self.max_anisotrophy = i
            self.mark_modified()

    def setClampBiasStr(self, value):
        val = validBool(value)
        if val != self.clamp_bias:
            self.clamp_bias = val
            self.mark_modified()

    def setTexelInterpolateStr(self, value):
        val = validBool(value)
        if val != self.texel_interpolate:
            self.texel_interpolate = val
            self.mark_modified()

    def setProjectionStr(self, value):
        i = indexListItem(self.PROJECTION, value, self.projection)
        if i >= 0:
            self.projection = i
            self.mark_modified()

    def setInputFormStr(self, value):
        i = indexListItem(self.INPUTFORM, value, self.inputform)
        if i >= 0:
            self.inputform = i
            self.mark_modified()

    def setTypeStr(self, value):
        i = indexListItem(self.TYPE, value, self.type)
        if i >= 0:
            self.type = i
            self.mark_modified()

    def setCoordinatesStr(self, value):
        i = indexListItem(self.COORDINATES, value, self.coordinates)
        if i >= 0:
            self.coordinates = i
            self.mark_modified()

    def setEmbossSourceStr(self, value):
        i = int(value)
        if not 0 <= i <= 7:
            raise ValueError("Value '" + value + "' out of range for emboss source")
        if self.emboss_source != i:
            self.emboss_source = i
            self.mark_modified()

    def setEmbossLightStr(self, value):
        i = int(value)
        if not 0 <= i <= 255:
            raise ValueError("Value '" + value + "' out of range for emboss light")
        if self.emboss_light != i:
            self.emboss_light = i
            self.mark_modified()

    def setNormalizeStr(self, value):
        val = validBool(value)
        if val != self.normalize:
            self.normalize = val
            self.mark_modified()

    def setLayerFlags(self, nibble):
        """ from lsb, enable, scaledefault, rotationdefault, transdefault """
        self.enable = nibble & 1
        if nibble >> 1 & 1:
            self.scale = (1, 1)
        if nibble >> 2 & 1:
            self.rotation = 0
        if nibble >> 3 & 1:
            self.translation = (0, 0)
        return self.enable

    def setName(self, value):
        if value != self.name:
            self.name = self.parent.renameLayer(self, value)
            self.mark_modified()

    SET_SETTING = (setScaleStr, setRotationStr, setTranslationStr, setCameraRefStr,
                   setLightRefStr, setMapmodeStr, setUWrapStr, setVWrapStr, setMinFilterStr, setMagFilterStr,
                   setLodBiasStr, setAnisotrophyStr, setClampBiasStr, setTexelInterpolateStr, setProjectionStr,
                   setInputFormStr, setTypeStr, setCoordinatesStr, setEmbossSourceStr, setEmbossLightStr,
                   setNormalizeStr, setName)

    def __str__(self):
        return self.name + ': srt:{} {} {}'.format(self.scale, self.rotation, self.translation)

    # -------------------------------------- PASTE ---------------------------
    def paste(self, item):
        if self.name == 'Null':
            self.setName(item.name)
        self.uwrap = item.uwrap
        self.vwrap = item.vwrap
        self.minfilter = item.minfilter
        self.magfilter = item.magfilter
        self.lod_bias = item.LODBias
        self.max_anisotrophy = item.max_anisotrophy
        self.clamp_bias = item.clamp_bias
        self.texel_interpolate = item.texel_interpolate
        self.scale = (item.scale[0], item.scale[1])
        self.rotation = item.rotation
        self.translation = (item.translation[0], item.translation[1])
        self.scn0_camera_ref = item.scn0_camera_ref
        self.scn0_light_ref = item.scn0_light_ref
        self.map_mode = item.map_mode
        self.enable_identity_matrix = item.enable_identity_matrix
        self.texture_matrix = copy(item.texture_matrix)
        self.projection = item.projection
        self.inputform = item.inputform
        self.type = item.type
        self.coordinates = item.coordinates
        self.emboss_source = item.emboss_source
        self.emboss_light = item.emboss_light
        self.dual_matrix = item.dual_matrix
        self.normalize = item.normalize
        self.mark_modified()

    def info(self, key=None, indentation_level=0):
        trace = '  ' * indentation_level + self.name if indentation_level else '>' + self.parent.name + "->" + self.name
        if key:
            val = self.get_str(key)
            print("{}\t{}:{}".format(trace, key, val))
        else:
            print("{}:\tScale:{} Rot:{} Trans:{}".format(
                trace, self.scale, self.rotation, self.translation))

    def uses_mipmaps(self):
        return self.minfilter > 1

    def set_minfilter(self, value):
        if self.minfilter != value:
            self.minfilter = value
            self.mark_modified()

    def check(self, texture_map=None):
        if texture_map is None:
            texture_map = self.parent.get_texture_map()
        tex = texture_map.get(self.name)
        if not tex:
            # try fuzz
            result = None
            b = Bug(2, 3, 'No texture matching {}'.format(self.name), '')
            if self.RENAME_UNKNOWN_REFS:
                result = fuzzy_strings(self.name, texture_map)
                if result is not None:
                    b.fix_des = 'Rename to {}'.format(result)
                    self.setName(result)
                    b.resolve()
                    tex = texture_map.get(self.name)
                    self.mark_modified()
            if result is None:
                if self.REMOVE_UNKNOWN_REFS:
                    b.fix_des = 'Remove reference'
                    self.parent.removeLayer(self.name)
                    b.resolve()
                    self.mark_modified()
                    return
        if tex:
            if self.uses_mipmaps():
                if tex.num_mips == 0:
                    b = Bug(4, 4, '{} no mipmaps in tex0'.format(self.name), 'Set minfilter to linear')
                    if self.MINFILTER_AUTO:
                        self.set_minfilter(1)  # linear
                        b.resolve()
                        self.mark_modified()
            else:
                if tex.num_mips > 0:
                    b = Bug(4, 4, '{} mipmaps disabled but TEX0 has {}'.format(
                        self.name, tex.num_mips), 'Set minfilter to LinearMipmapLinear')
                    if self.MINFILTER_AUTO:
                        self.set_minfilter(5) # linearmipmaplinear
                        b.resolve()
                        self.mark_modified()
