#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
#   Robert Nelson
# -------------------------------------------------------------------
from unpack import *
from material import *
from pack import *
import re  # yeah regexs are in
import fnmatch
import sys, getopt
import os

VERSION = "0.1.0"
USAGE = "{} -f <file> [-d <destination> -o -c <commandfile> -k <key> -v <value> -n <name> -m <model> -i] "


class Command:
    def __init__(self, cmd, key, value, name, file, model, material):
        self.cmd = cmd
        self.key = key
        self.value = value
        self.name = name
        self.filename = file
        self.modelname = model
        self.materialname = material

def load_commandfile(filename):
    if not os.path.exists(filename):
        print("No such file {}".format(filename))
        exit(2)
    f = open(filename, "r")
    lines = f.readlines()
    regex = re.compile("(?P<cmd>\w+)\s+(?P<key>\w+)\s*:(?P<value>\S+)(\s+for\s+(?P<item>\S+))?(\s+in(\s+file\s+(?P<fname>\S+))?(\s+model\s+(?P<modelname>\S+))?(\s+material\s+(?P<matname>\S+))?)?")
    commands = []
    for line in lines:
        match = regex.match(line)
        if match:
            commands.append(Command(match["cmd"], match["key"].lower(), match["value"].lower(), match["item"], match["fname"], match["modelname"], match["matname"]))
    return commands

def getFiles(filename):
    directory = os.path.dirname(filename)
    print("Directory: {}".format(directory))
    files = []
    for file in os.listdir(directory):
        if fnmatch.fnmatch(file, filename):
            files.append(file)
    return files

def openFiles(filenames, openfiles):
    for f in filenames:
        if not openFiles[f]:
            openFiles[f] = Brres(f)

def closeFiles(excludenames, openfiles, destination, overwrite):
    for fname, brres in openfiles:
        if not fname in excludenames:
            brres.save(destination, overwrite)


def validate_cmds(commandlist, destination):
    if not commandlist:
        print("No commands detected")
        return False
    file = ""
    count = 0
    for cmd in commandlist:
        cmd.key = cmd.key.lower()
        cmd.cmd = cmd.cmd.lower()
        cmd.value = cmd.value.lower()
        if count == 0 and not cmd.filename:
            print("File is required to run commands!")
            return False
        count += 1
        try:
            i = Brres.COMMANDS.index(cmd)
            if i == 0:
                if not cmd.key in Material.SETTINGS and not cmd.key in Layer.SETTINGS:
                    print("Unknown Key {}".format(cmd.key))
                    return False
        except ValueError:
            print("Unknown command {}".format(cmd.cmd))
            return False
        if cmd.filename:
            files = getFiles(cmd.filename)
            if not files: # could possibly ignore error here for wildcard patterns?
                print("The file '{}' does not exist", cmd.filename)
                return False
            elif destination and len(files) > 1 or file and files[0] != file:
                print("Error: Multiple files for single destination!")
                print("Specify single file and destination, or no destination with overwrite option.")
                return False
            elif not file:
                file = files[0]
    return count


def run_commands(commandlist, destination, overwrite):
    if not validate_cmds(commandlist, destination):
        sys.exit(1)
    openFiles = {}
    for cmd in commandlist:
        if cmd.filename:
            filenames = getFiles(cmd.filename)
            closeFiles(filenames, openFiles, destination, overwrite)
            openFiles(filenames, openFiles)
        brres.parseCommand(cmd)
    closeFiles(None, openFiles, destination, overwrite)


class Brres:
    LAYERSETTINGSINDEX = 32
    COMMANDS = ["set", "info"]
    # Future shader stuff, blend mode and alpha func
    def __init__(self, fname):
        self.filename = fname
        self.brres = UnpackBrres(fname)
        self.models = self.brres.models
        self.isModified = False
        self.isUpdated = False

    def getModelsByName(self, name):
        return findAll(name, self.models)

    def save(self, filename, overwrite):
        if not filename:
            filename = self.filename
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            if self.isChanged():
                PackBrres(self)
            packed = self.brres.file.file
            f = open(filename, "wb")
            f.write(packed)
            f.close()
            print("Wrote file '{}'".format(filename))
            return True

    def setModel(self, modelname):
        for mdl in self.models:
            if modelname == mdl.name:
                self.model = mdl
                return True
        regex = re.compile(modelname)
        if regex:
            for mdl in self.models:
                if regex.search(modelname):
                    self.model = mdl
                    return True
        return False

    def parseCommand(self, command):
        if command.cmd == self.COMMANDS[0]:
            self.set(command)
        elif command.cmd == self.COMMANDS[1]:
            self.info(command)
        else:
            print("Unknown command: {}".format(self.cmd))

    def info(self, command):
        if command.key:
            mats = self.getMatCollection(command.modelname, command.materialname)
            if command.key in Layer.SETTINGS:
                layers = self.getLayerCollection(mats, command.name)
                for layer in layers:
                    layer.info(command)
            elif command.key in Material.SETTINGS:
                mats = findAll(command.name, mats)
                for mat in mats:
                    mat.info(command)
            else:
                print("Unknown command key {}".format(command.key))
        else:
            mdls = findAll(command.name, self.models)
            for mdl in mdls:
                mdl.info(command)
            mats = self.getMatCollection(command.modelname, command.materialname)
            matches = findAll(command.name, mats)
            for mat in matches:
                mat.info(command)
            layers = self.getLayerCollection(mats, command.name)
            for layer in layers:
                layer.info(command)

    def set(self, command):
        mats = self.getMatCollection(command.modelname, command.materialname)
        if command.key in Layer.SETTINGS:
            layers = self.getLayerCollection(mats, command.name)
            self.layersSet(layers, command.key, command.value)
        else:
            mats = findAll(command.name, mats)
            self.materialSet(mats, command.key, command.value)


    def getModelByOffset(self, offset):
        for mdl in self.models:
            if offset == mdl.offset:
                return mdl


    def getMatCollection(self, modelname, materialname):
        mdls = findAll(modelname, self.brres.models)
        mats = []
        for mdl in mdls:
            mats = mats + findAll(materialname, mdl.mats)
        return mats

    def getLayerCollection(self, mats, layername):
        layers = []
        for m in mats:
            layers = layers + findAll(layername, m.layers)
        return layers

    def materialSet(self, materials, setting, value):
        settingIndex = Material.SETTINGS.index(setting)
        if settingIndex < 0:
            print("Unknown setting {}".format(setting))
            return False
        try:
            # Ugly ugly ugly!
            if settingIndex < 2: # XLU
                for x in materials:
                    x.setTransparentStr(value)
            elif settingIndex == 2: # Ref0
                for x in materials:
                    x.setRef0Str(value)
            elif settingIndex == 3: # Ref1
                for x in materials:
                    x.setRef1Str(value)
            elif settingIndex == 4: # Comp0
                for x in materials:
                    x.setComp0Str(value)
            elif settingIndex == 5: # Comp1
                for x in materials:
                    x.setComp1Str(value)
            elif settingIndex == 6: # CompareBeforeTexture
                for x in materials:
                    x.setCompareBeforeTexStr(value)
            elif settingIndex == 7: # Blend
                for x in materials:
                    x.setBlendStr(value)
            elif settingIndex == 8: # blendsrc
                for x in materials:
                    x.setBlendSrcStr(value)
            elif settingIndex == 9: # blendlogic
                for x in materials:
                    x.setBlendLogicStr(value)
            elif settingIndex == 10: # blenddest
                for x in materials:
                    x.setBlendDestStr(value)
            elif settingIndex == 11:    # constant alpha
                for x in materials:
                    x.setConstantAlphaStr(value)
            elif settingIndex == 12: # CULL Mode
                for x in materials:
                    x.setCullModeStr(value)
            elif settingIndex == 13: # Shader
                shaderindex = int(value)
                for x in materials:
                    # may be a more efficent way to do this
                    mdl = self.getModelByOffset(x.getMdlOffset())
                    shader = mdl.getTev(shaderindex)
                    if not shader:
                        raise ValueError("Shader '{}' does not exist in model '{}'!".format(shaderindex, mdl.name))
                    x.setShader(shader)
                    # update shader material entry
                    mdl.updateTevEntry(shader, x)
            elif settingIndex == 14:    # shader color
                for x in materials:
                    x.setShaderColorStr(value)
            elif settingIndex == 15: #Light Channel
                for x in materials:
                    x.setLightChannelStr(value)
            elif settingIndex == 16: #Light set
                for x in materials:
                    x.setLightsetStr(value)
            elif settingIndex == 17: #Fog set
                for x in materials:
                    x.setFogsetStr(value)
            elif settingIndex == 18: # matrix mode
                for x in materials:
                    x.setMatrixModeStr(value)
            elif settingIndex == 19:    # enableDepthTest
                for x in materials:
                    x.setEnableDepthTestStr(value)
            elif settingIndex == 20:    #enableDepthUpdate
                for x in materials:
                    x.setEnableDepthUpdateStr(value)
            elif settingIndex == 21:    # depth function
                for x in materials:
                    x.setDepthFunctionStr(value)
            elif settingIndex == 22:    # draw priority
                for x in materials:
                    x.setDrawPriorityStr(value)
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        self.isUpdated = True
        return True

    def layersSet(self, layers, setting, value):
        try:
            settingIndex = Layer.SETTINGS.index(setting)
            if settingIndex < 0:
                print("Unknown setting {}".format(setting))
                return False
            if settingIndex == 0:  # Scale
                for x in matches:
                    x.setScaleStr(value)
            elif settingIndex == 1:  # rotation
                for x in matches:
                    x.setRotationStr(value)
            elif settingIndex == 2:    # translation
                for x in matches:
                    x.setTranslationStr(value)
            elif settingIndex == 3:    # scn-32CameraRef
                for x in matches:
                    x.setCameraRefStr(value)
            elif settingIndex == 4:    # lightRef
                for x in matches:
                    x.setLightRefStr(value)
            elif settingIndex == 5:    # mapmode
                for x in matches:
                    x.setMapmodeStr(value)
            elif settingIndex == 6:    # uwrap
                for x in matches:
                    x.setUWrapStr(value)
            elif settingIndex == 7:    #vwrap
                for x in matches:
                    x.setVWrapStr(value)
            elif settingIndex == 8:    # minfilter
                for x in matches:
                    x.setMinFilterStr(value)
            elif settingIndex == 9:    # magfilter
                for x in matches:
                    x.setMagFilterStr(value)
            elif settingIndex == 10:    #  lodbias
                for x in matches:
                    x.setLodBiasStr(value)
            elif settingIndex == 11:    # anisotrophy
                for x in matches:
                    x.setAnisotrophyStr(value)
            elif settingIndex == 12:    # clampbias
                for x in matches:
                    x.setClampBiasStr(value)
            elif settingIndex == 13:    # texelInterpolate
                for x in matches:
                    x.setTexelInterpolateStr(value)
            elif settingIndex == 14:    # projection
                for x in matches:
                    x.setProjectionStr(value)
            elif settingIndex == 15:    # inputform
                for x in matches:
                    x.setInputFormStr(value)
            elif settingIndex == 16:    # type
                for x in matches:
                    x.setTypeStr(value)
            elif settingIndex == 17:    # coordinates
                for x in matches:
                    x.setCoordinatesStr(value)
            elif settingIndex == 18:    # embosssource
                for x in matches:
                    x.setEmbossSourceStr(value)
            elif settingIndex == 19:    # embosslight
                for x in matches:
                    x.setEmbossLightStr(value)
            elif settingIndex == 20:    # normalize
                for x in matches:
                    x.setNormalizeStr(value)
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        self.isUpdated = True
        return True

    def isChanged(self):
        if self.isModified:
            return True
        if self.isUpdated:
            for mdl in self.models:
                if mdl.isChanged():
                    self.isModified = True # to prevent checking further
                    return True
        self.isUpdated = False
        return False

    def list_materials(self):
        mats = self.model.mats
        print("Materials:")
        for mat in mats:
            print("\t{}".format(mat.name))

def help():
    help  = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}

      >>       >==>    >=>     >===>          >===>      >=>>=>    >=>   >=>>=>
     >>=>      >> >=>  >=>   >=>    >=>     >=>    >=>   >>   >=>   >> >=>    >=>
    >> >=>     >=> >=> >=> >=>        >=> >=>        >=> >>    >=>      >=>
   >=>  >=>    >=>  >=>>=> >=>        >=> >=>        >=> >==>>=>          >=>
  >=====>>=>   >=>   > >=> >=>        >=> >=>        >=> >>    >=>           >=>
 >=>      >=>  >=>    >>=>   >=>     >=>    >=>     >=>  >>     >>     >=>    >=>
>=>        >=> >=>     >=>     >===>          >===>      >===>>=>        >=>>=>

>=>>=>    >======>     >======>     >=======>   >=>>=>
>>   >=>  >=>    >=>   >=>    >=>   >=>       >=>    >=>
>>    >=> >=>    >=>   >=>    >=>   >=>        >=>
>==>>=>   >> >==>      >> >==>      >=====>      >=>
>>    >=> >=>  >=>     >=>  >=>     >=>             >=>
>>     >> >=>    >=>   >=>    >=>   >=>       >=>    >=>
>===>>=>  >=>      >=> >=>      >=> >=======>   >=>>=>

>=>       >=>       >>       >===>>=====> >=======> >======>     >=>       >>       >=>
>> >=>   >>=>      >>=>           >=>     >=>       >=>    >=>   >=>      >>=>      >=>
>=> >=> > >=>     >> >=>          >=>     >=>       >=>    >=>   >=>     >> >=>     >=>
>=>  >=>  >=>    >=>  >=>         >=>     >=====>   >> >==>      >=>    >=>  >=>    >=>
>=>   >>  >=>   >=====>>=>        >=>     >=>       >=>  >=>     >=>   >=====>>=>   >=>
>=>       >=>  >=>      >=>       >=>     >=>       >=>    >=>   >=>  >=>      >=>  >=>
>=>       >=> >=>        >=>      >=>     >=======> >=>      >=> >=> >=>        >=> >=======>

>===>>=====>     >===>          >===>      >=>
     >=>       >=>    >=>     >=>    >=>   >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>       >=>     >=>    >=>     >=>  >=>
     >=>         >===>          >===>      >=======>
====================================================================================

ABMatT is a tool for editing materials in Mario Kart Wii 'Brres' files. The tool can
do quick edits from the command line, or read in a command file for processing multiple
setting adjustments. This is particularly useful for editing a large
amount of materials or recreating a brres multiple times. Python regex matching is supported.
The tool is also smart about adjusting transparency. When setting to transparent it also
updates the comparison and reference settings, and the draw list to be xlu (fixing Harry Potter effect).

File command format in extended BNF:
    command = set | info;
    set   = 'set' space key ':' value [space 'for' space name] [space 'in' space container] EOL;
    info  = 'info' [space key] [space 'for' space name] [space 'in' space container] EOL;

Example file commands:
    set transparent:true for xlu.* in model course      # Sets all materials in course starting with xlu to transparent
    set shader:3 for ef_dushboard   # set any material in any model found matching 'ef_dushboard' to shader 3
    set scale:(1,1)                 # Sets the scale for all layers to 1,1
Example command line usage:
    ./AbMatT.py -f course_model.brres -o -k xlu -v disable -n opaque_material
This opens course_model.brres in overwrite mode and disables transparency for material 'opaque_material'.
For more Help or if you want to contribute visit https://github.com/Robert-N7/ABMatT
    '''
    print(help.format(VERSION))
    print("Usage: {}".format(USAGE))


def main(argv):

    try:
        opts, args = getopt.getopt(argv, "hf:d:ok:v:n:m:c:i",
         ["help", "file=", "destination=", "overwrite", "key=", "value=",
         "name=", "model=", "info", "commandfile="])
    except getopt.GetoptError:
        print(USAGE)
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
        elif opt in ("-k", "--key"):
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
            print(USAGE)
            sys.exit(2)
    if not filename:
        print("Filename is required")
        print(USAGE)
        sys.exit(2)
    if not os.path.exists(filename):
        print("File '{}' does not exist.".format(filename))
        sys.exit(1)

    if info or not setting:
        cmd = "info"
        cmds = [Command(cmd, setting, value, name, filename, model, None)]
    else:
        cmd = "set"
        cmds = [Command(cmd, setting, value, name, filename, model, None)]
        if info:
            cmds.append(Command("info", setting, value, name, filename, model, None))
    run_commands(cmds, None, destination, overwrite)
    # interactive mode maybe?

# finds a name in group, group instances must have .name
def findAll(name, group):
    if not name or name == "*":
        return group
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
            items.append(item)
    if(len(items)):
        return items
    return None

if __name__ == "__main__":
    USAGE = USAGE.format(sys.argv[0])
    main(sys.argv[1:])
