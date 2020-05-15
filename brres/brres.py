#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
# -------------------------------------------------------------------
from unpack import *
from material import *
from pack import *
import re  # yeah regexs are in
import sys, getopt
import os.path

class Brres:
    LAYERSETTINGSINDEX = 32
    SETTINGS = ["xlu", "transparent", "ref0", "ref1", #4
    "comp0", "comp1", "comparebeforetexture", "blend", #8
    "blendsrc", "blendlogic", "blenddest", "constantalpha",
    "cullmode", "shader", "shadercolor", "lightchannel", #16
    "lightset", "fogset", "matrixmode", "enabledepthtest",
    "enabledepthupdate", "depthfunction", "drawpriority", "filler1" #24
    "filler1", "filler1", "filler1", "filler1",
    "filler1", "filler1", "filler1", "filler1", #32
    # start layer settings 32
    "scale", "rotation", "translation", "scn0cameraref",
    "scn0lightref", "mapmode", "uwrap", "vwrap",    #40
    "minfilter", "magfilter", "lodbias", "anisotrophy",
    "clampbias", "texelinterpolate", "projection", "inputform", #48
    "type", "coordinates", "embosssource", "embosslight",
    "normalize"]
    # Future shader stuff, blend mode and alpha func
    def __init__(self, fname):
        self.brres = UnpackBrres(fname)
        self.model = self.brres.models[0]
        self.isModified = False


    def getMaterialsByName(self, name):
        return findAll(name, self.model.mats)

    def getLayersByName(self, name):
        mats = self.model.mats
        layers = []
        for mat in mats:
            for layer in mat.layers:
                layers.append(layer)
        return findAll(name, layers)

    def save(self, filename, overwrite):
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            if self.isChanged():
                packed = PackBrres(self).file.file
            else:
                packed = self.brres.file.file
            f = open(filename, "wb")
            f.write(packed)
            f.close()
            print("Wrote file '{}'".format(filename))
            return True

    def setModel(self, modelname):
        self.isChanged() # check if the materials were modified
        for mdl in self.brres.models:
            if modelname == mdl.name:
                self.model = mdl
                return True
        regex = re.compile(modelname)
        if regex:
            for mdl in self.brres.models:
                if regex.search(modelname):
                    self.model = mdl
                    return True
        return False

    def parseSetting(self, setting, refname, value):
        settingIndex = -1
        setting = setting.lower()
        value = value.lower()
        for i in range(len(self.SETTINGS)):
            if(self.SETTINGS[i] == setting):
                settingIndex = i
                break
        if settingIndex == -1:
            print("Unkown setting '{}'".format(setting))
            return False
        try:
            if settingIndex < self.LAYERSETTINGSINDEX:
                matches = self.getMaterialsByName(refname)
                # Ugly ugly ugly!
                if settingIndex < 2: # XLU
                    for x in matches:
                        setTranslationStr(value)
                elif settingIndex == 2: # Ref0
                    for x in matches:
                        x.setRef0Str(value)
                elif settingIndex == 3: # Ref1
                    for x in matches:
                        x.setRef1Str(value)
                elif settingIndex == 4: # Comp0
                    for x in matches:
                        x.setComp0Str(value)
                elif settingIndex == 5: # Comp1
                    for x in matches:
                        x.setComp1Str(value)
                elif settingIndex == 6: # CompareBeforeTexture
                    for x in matches:
                        x.setCompareBeforeTexStr(value)
                elif settingIndex == 7: # Blend
                    for x in matches:
                        x.setBlendStr(value)
                elif settingIndex == 8: # blendsrc
                    for x in matches:
                        x.setBlendSrcStr(value)
                elif settingIndex == 9: # blendlogic
                    for x in matches:
                        x.setBlendLogicStr(value)
                elif settingIndex == 10: # blenddest
                    for x in matches:
                        x.setBlendDestStr(value)
                elif settingIndex == 11:    # constant alpha
                    for x in matches:
                        x.setConstantAlphaStr(value)
                elif settingIndex == 12: # CULL Mode
                    for x in matches:
                        x.setCullModeStr(value)
                elif settingIndex == 13: # Shader
                    for x in matches:
                        x.setShaderStr(value)
                elif settingIndex == 14:    # shader color
                    for x in matches:
                        x.setShaderColorStr(value)
                elif settingIndex == 15: #Light Channel
                    for x in matches:
                        x.setLightChannelStr(value)
                elif settingIndex == 16: #Light set
                    for x in matches:
                        x.setLightsetStr(value)
                elif settingIndex == 17: #Fog set
                    for x in matches:
                        x.setFogsetStr(value)
                elif settingIndex == 18: # matrix mode
                    for x in matches:
                        x.setMatrixModeStr(value)
                elif settingIndex == 19:    # enableDepthTest
                    for x in matches:
                        x.setEnableDepthTestStr(value)
                elif settingIndex == 20:    #enableDepthUpdate
                    for x in matches:
                        x.setEnableDepthUpdateStr(value)
                elif settingIndex == 21:    # depth function
                    for x in matches:
                        x.setDepthFunctionStr(value)
                elif settingIndex == 22:    # draw priority
                    for x in matches:
                        x.setDrawPriorityStr(value)

            else:
                matches = self.getLayersByName(refname)
                if settingIndex == 32:  # Scale
                    for x in matches:
                        x.setScaleStr(value)
                elif settingIndex == 33:  # rotation
                    for x in matches:
                        x.setRotationStr(value)
                elif settingIndex == 34:    # translation
                    for x in matches:
                        x.setTranslationStr(value)
                elif settingIndex == 35:    # scn0CameraRef
                    for x in matches:
                        x.setCameraRefStr(value)
                elif settingIndex == 36:    # lightRef
                    for x in matches:
                        x.setLightRefStr(value)
                elif settingIndex == 37:    # mapmode
                    for x in matches:
                        x.setMapmodeStr(value)
                elif settingIndex == 38:    # uwrap
                    for x in matches:
                        x.setUWrapStr(value)
                elif settingIndex == 39:    #vwrap
                    for x in matches:
                        x.setVWrapStr(value)
                elif settingIndex == 40:    # minfilter
                    for x in matches:
                        x.setMinFilterStr(value)
                elif settingIndex == 41:    # magfilter
                    for x in matches:
                        x.setMagFilterStr(value)
                elif settingIndex == 42:    #  lodbias
                    for x in matches:
                        x.setLodBiasStr(value)
                elif settingIndex == 43:    # anisotrophy
                    for x in matches:
                        x.setAnisotrophyStr(value)
                elif settingIndex == 44:    # clampbias
                    for x in matches:
                        x.setClampBiasStr(value)
                elif settingIndex == 45:    # texelInterpolate
                    for x in matches:
                        x.setTexelInterpolateStr(value)
                elif settingIndex == 46:    # projection
                    for x in matches:
                        x.setProjectionStr(value)
                elif settingIndex == 47:    # inputform
                    for x in matches:
                        x.setInputFormStr(value)
                elif settingIndex == 48:    # type
                    for x in matches:
                        x.setTypeStr(value)
                elif settingIndex == 49:    # coordinates
                    for x in matches:
                        x.setCoordinatesStr(value)
                elif settingIndex == 50:    # embosssource
                    for x in matches:
                        x.setEmbossSourceStr(value)
                elif settingIndex == 51:    # embosslight
                    for x in matches:
                        x.setEmbossLightStr(value)
                elif settingIndex == 52:    # normalize
                    for x in matches:
                        x.setNormalizeStr(value)
        except ValueError as e:
            print(str(e))
            sys.exit(1)


    def isChanged(self):
        if self.isModified:
            return True
        if self.model.isChanged():
            self.isModified = True # to prevent checking further
            return True
        return False

    def info(self, name):
        print("Here's some info, you're welcome")
        self.list_materials()
        # todo

    def list_materials(self):
        mats = self.model.mats
        print("Materials:")
        for mat in mats:
            print("\t{}".format(mat.name))

def help():
    print("This is helpful.")
    # todo

    # todo read in file of commands option
def main(argv):
    usage = "brres.py -f <file> [-d <destination> -o -c <commandfile> -s <setting> -v <value> -n <name> -m <model> -i] "
    try:
        opts, args = getopt.getopt(argv, "hf:d:os:v:n:m:c:", ["help", "file=", "destination=", "overwrite", "setting=", "value=", "name=", "model=", "info", "commandfile="])
    except getopt.GetoptError:
        print(usage)
        sys.exit(2)
    filename = ""
    destination = ""
    overwrite = False
    setting = ""
    value = ""
    name = ".*"
    model = ""
    commandfile = ""
    info = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help()
            sys.exit()
        elif opt in ("-f", "--file"):
            filename = arg
        elif opt in ("-d", "--destination"):
            destination = arg
        elif opt in ("-o", "--overwrite"):
            overwrite = True
        elif opt in ("-s", "--setting"):
            setting = arg
        elif opt in ("-v", "--value"):
            value = arg
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-m", "--model"):
            model = arg
        elif opt in ("-i", "--info"):
            info = True
        elif opt in ("-c", "--commandfile"):
            commandfile = arg
        else:
            print("Unknown option '{}'".format(opt))
            print(usage)
            sys.exit(2)
    if not filename:
        print("Filename is required")
        print(usage)
        sys.exit(2)
    if not os.path.exists(filename):
        print("File '{}' does not exist.".format(filename))
        sys.exit(1)

    brres = Brres(filename)
    if model:
        brres.setModel(model)
    if setting:
        brres.parseSetting(setting, name, value)
    if info or not setting:
        brres.info(name)
    if brres.isChanged() or destination:
        brres.save(destination, overwrite)
    # interactive mode maybe?

# finds a name in group, group instances must have .name
def findAll(name, group):
    items = []
    try:
        regex = re.compile(name)
        for item in group:
            if regex.search(item.name):
                items.append(item)
    except re.error:
        pass
    # direct matching?
    for item in group:
        if item.name == name:
            item.append(item)
    if(len(items)):
        return items
    return None

if __name__ == "__main__":
    main(sys.argv[1:])
