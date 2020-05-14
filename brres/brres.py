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
    LAYERSETTINGSINDEX = 20
    SETTINGS = ["xlu", "transparent", "cullmode", "lightchannel",
    "lightset", "fogset", "alpha", "matrixmode",
    "activestages", "indirectstages", "comparebeforetexture", "enabledepthtest",
    "enabledepthupdate", "filler1", "filler1", "filler1",
    "filler1", "filler1", "filler1", "filler1",
    "scale", "rotation", "translation", "scn0cameraref",
    "scn0lightref", "mapmode", "uwrap", "vwrap",
    "minfilter", "magfilter", "lodbias", "anisotrophy",
    "clampbias", "texelinterpolate"]
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
            packed = PackBrres(self)
            f = open(filename, "wb")
            f.write(f)
            f.close()
            print("Wrote file '{}'".format(filename))
            return True

    def setModel(self, modelname):
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
        for i in range(len(self.SETTINGS)):
            if(self.SETTINGS[i] == setting):
                settingIndex = i
                break
        if settingIndex == -1:
            print("Unkown setting '{}'".format(setting))
            return False
        if settingIndex >= self.LAYERSETTINGSINDEX:
            matches = self.getLayersByName(refname)
            if settingIndex < 2: # XLU
                for x in matches:
                    if value and value is not "false":
                        x.setTransparent()
                    else:
                        x.setOpaque()

            elif settingIndex == 3: # CULL Mode
                try:
                    for x in matches:
                        x.setCullModeStr(value)
                except ValueError as e:
                    print(str(e))
                    print("Valid modes are 'all|inside|outside|none'")
                    sys.exit(1)
            elif settingIndex == 4: #Light Channel
                try:
                    for x in matches:
                        pass
                except ValueError as e:
                    pass

            elif settingIndex == 5:
                pass    # todo
            elif settingIndex == 6:
                pass    # todo
            elif settingIndex == 7:
                pass    # todo
            elif settingIndex == 8:
                pass    # todo
            elif settingIndex == 9:
                pass    # todo
            elif settingIndex == 10:
                pass    # todo
            elif settingIndex == 11:
                pass    # todo
            elif settingIndex == 12:
                pass    # todo
        else:
            matches = self.getMaterialsByName(refname)
            if settingIndex == 13:
                pass    # todo
            elif settingIndex == 14:
                pass    # todo
            elif settingIndex == 15:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo
            elif settingIndex == n:
                pass    # todo


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

def main(argv):
    usage = "brres.py -f <file> [-d <destination> -o -s <setting> -v <value> -n <name> -m <model> -i] "
    try:
        opts, args = getopt.getopt(argv, "hf:d:os:v:n:m:", ["help", "file=", "destination=", "overwrite", "setting=", "value=", "name=", "model=", "info"])
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

    b = Brres(filename)
    if model:
        b.setModel(model)
    if setting:
        b.parseSetting(setting, name, value)
    if info or not setting:
        b.info(name)
    if b.isModified or destination:
        b.save(destination, overwrite)
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
