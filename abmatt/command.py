# ---------------------------------------------------------------------------
# Command class and functions
# ---------------------------------------------------------------------------
import fnmatch
import os
import sys

from brres import Brres
from matching import *
from mdl0.layer import Layer
from mdl0.material import Material
from mdl0.shader import Shader, Stage
from srt0.srt0 import Srt0


class ParsingException(Exception):
    def __init__(self, txt, message=''):
        super(ParsingException, self).__init__("Error parsing: '" + txt + "' " + message)


def getShadersFromMaterials(materials, models, for_modification=True):
    """Gets unique shaders from material list, where materials may come from different models,
        may have to detach if shared with material not in list
    """
    shaders = []
    for x in models:
        shaders.extend(x.getShaders(materials, for_modification))
    return shaders


class Command:
    COMMANDS = ["preset", "set", "add", "remove", "info", "select"]
    SELECTED = []  # selection list
    SELECT_TYPE = None  # current selection list type
    DESTINATION = None
    OVERWRITE = False
    ACTIVE_FILES = []
    MODELS = []
    MATERIALS = []
    PRESETS = {}

    TYPE_SETTING_MAP = {
        "material": Material.SETTINGS,
        "layer": Layer.SETTINGS,
        "shader": Shader.SETTINGS,
        "stage": Stage.SETTINGS,
        "srt0": Srt0.SETTINGS
    }

    def __init__(self, text):
        """ parses the text as a command """
        self.hasSelection = False
        self.name = self.key = None
        self.txt = text.strip('\r\n')
        self.type_id = 0
        self.type_id_numeric = True
        x = [x.strip() for x in text.split()]
        if not x:
            raise ParsingException(self.txt, 'No Command detected')
        is_preset = self.setCmd(x.pop(0).lower())
        if not x:
            raise ParsingException(self.txt, 'Not enough parameters')
        if self.setType(x[0]):
            x.pop(0)
        for_index = -1
        for i in range(len(x)):
            if x[i].lower() == 'for':
                for_index = i
                break
        if for_index >= 0:
            self.setSelection(x[for_index:])
            x = x[0:for_index]
        if is_preset:
            key = x[0]
            if key not in self.PRESETS:
                raise ParsingException(self.txt, 'No such preset {}'.format(key))
            self.key = key
            return
        elif self.cmd == 'set':
            if not x:
                raise ParsingException(self.txt, 'Not enough parameters')
            if ':' not in x[0]:
                raise ParsingException(self.txt, 'Set requires key:value pair')
            key, value = x[0].split(':', 1)
            self.key = key.lower()
            self.value = value.lower()
        elif len(x):
            if self.cmd != 'info':
                print("Unknown parameter(s) {}".format(x))
            else:
                self.key = x[0].lower()
        if self.key and self.type and self.key not in self.TYPE_SETTING_MAP[self.type]:
            raise ParsingException(self.txt, "Unknown Key {} for {}, possible keys:\n\t{}".format(self.key, self.type,
                                                                                                  self.TYPE_SETTING_MAP[
                                                                                                      self.type]))

    def setType(self, val):
        """Returns true if the type is set by val"""
        if self.cmd == 'preset':
            self.type = 'material'
            return False
        i = val.find(':')
        if i > 0 and len(val) > i + 1:
            type_id = val[i + 1:]
            try:
                self.type_id = validInt(type_id, 0, 16)
                self.type_id_numeric = True
            except ValueError:
                self.type_id = type_id
                self.type_id_numeric = False
            val = val[:i]
        self.type = val.lower()
        if val == 'material' or val == 'shader':
            if self.cmd == 'add' or self.cmd == 'remove':
                raise ParsingException(self.txt, 'Add/Remove not supported for materials and shaders.')
        elif val == 'layer' or val == 'stage':
            pass
        # elif 'srt0' in val:
        #     self.type = 'srt0'
        else:
            self.type = None
            return False
        return True

    def setSelection(self, li):
        """ takes a list beginning with 'for' and parses selection """
        if len(li) < 2:
            print("No selection given")
            self.hasSelection = False
            return False
        self.hasSelection = True
        self.name = li[1]
        self.model = self.file = x = None
        if len(li) > 2:
            if li[2] != 'in':
                raise ParsingException(self.txt, 'Expected "in"')
            li = li[3:]
            i = 0
            try:  # to get args
                while i < len(li):
                    x = li[i]
                    if x == 'file' or x == 'File':
                        i += 1
                        self.file = li[i]  # possible exception
                    elif x == 'model' or x == 'Model':
                        i += 1
                        self.model = li[i]
                    else:
                        raise ParsingException(self.txt, 'Unknown argument {}'.format(li[i]))
                    i += 1
            except IndexError:
                raise ParsingException(self.txt, "Argument required for " + x)

    def setCmd(self, val):
        if not val in self.COMMANDS:
            raise ParsingException(self.txt, "Unknown command '{}'".format(val))
        else:
            self.cmd = val
        return self.cmd == 'preset'

    @staticmethod
    def updateFile(filename):
        files = getFiles(filename)
        if not files:  # could possibly ignore error here for wildcard patterns?
            print("The file '{}' does not exist".format(filename))
            return False
        if Command.DESTINATION:  # check for multiple files with single destination
            outside_active = True
            for x in Command.ACTIVE_FILES:
                if files[0] == x.name:
                    outside_active = False
                    break
            if len(files) > 1 or Command.ACTIVE_FILES and outside_active:
                print("Error: Multiple files for single destination!")
                print("Specify single file and destination, or no destination with overwrite option.")
                return False
        Command.ACTIVE_FILES = openFiles(files, Command.ACTIVE_FILES)
        Command.MODELS = []  # clear models

    def updateSelection(self):
        """ updates container items """
        if self.file:
            self.updateFile(self.file)
        # Models
        if self.model or not self.MODELS:
            Command.MATERIALS = []  # reset materials
            for x in self.ACTIVE_FILES:
                Command.MODELS.extend(x.getModelsByName(self.model))
        # Materials
        for x in self.MODELS:
            Command.MATERIALS.extend(x.getMaterialsByName(self.name))
        Command.SELECT_TYPE = None  # reset selection
        return True

    @staticmethod
    def detectType(key):
        map = Command.TYPE_SETTING_MAP
        for x in map:
            if key in map[x]:
                return x

    def updateType(self):
        """ Updates the current selection by the type/cmd"""
        if self.cmd == 'add' or self.cmd == 'remove':  # use parents as selection
            type = 'shader' if self.type == 'stage' else 'material'
        else:
            if self.type:
                type = self.type
            elif self.SELECT_TYPE:
                type = self.SELECT_TYPE
            else:  # auto detect
                if self.key:
                    type = self.detectType(self.key)  # possibly ambiguous for stages/layers?
                    if not type:
                        raise ParsingException(self.txt, 'Unknown key {}!'.format(self.key))
                else:
                    type = 'material'
        if type != self.SELECT_TYPE:
            if type == 'material':
                Command.SELECTED = self.MATERIALS
            elif type == 'layer':
                if self.type_id_numeric:
                    Command.SELECTED = [x.getLayerI(self.type_id) for x in self.MATERIALS]
                else:
                    Command.SELECTED = []
                    for x in self.MATERIALS:
                        Command.SELECTED.extend(x.getLayers(self.type_id))
                    if not Command.SELECTED:  # Forcibly adding case if no selected found
                        # possible todo... make this optional?
                        Command.Selected = [x.forceAdd(self.type_id) for x in self.MATERIALS]

            # elif self.type == 'srt0':
            #     pass # todo
            elif type == 'shader' or type == 'stage':
                shaders = getShadersFromMaterials(self.MATERIALS, self.MODELS)
                if type == 'shader':
                    Command.SELECTED = shaders
                else:
                    Command.SELECTED = []
                    for x in shaders:
                        Command.SELECTED.append(x.getStage(self.type_id))
            elif self.cmd == 'info':
                if type == 'mdl0':
                    Command.SELECTED = self.MODELS
                elif type == 'brres':
                    Command.SELECTED = self.ACTIVE_FILES
            Command.SELECT_TYPE = type

    def runCmd(self):
        if self.hasSelection:
            if not self.updateSelection():
                sys.exit(1)
        self.updateType()
        if not self.ACTIVE_FILES:
            raise ParsingException(self.txt, 'No file detected!')
        if not self.SELECTED:
            print("No items found in selection for '{}'".format(self.txt))
        else:
            if self.cmd == 'set':
                for x in self.SELECTED:
                    x[self.key] = self.value
            elif self.cmd == 'info':
                for x in self.SELECTED:
                    x.info(self.key)
                # for y in self.ACTIVE_FILES:
                #     print(y.name)
            elif self.cmd == 'add':
                self.add(self.type, self.type_id)
            elif self.cmd == 'remove':
                self.remove(self.type, self.type_id)
            elif self.cmd == 'preset':
                self.runPreset(self.key)

    def runPreset(self, key):
        """Runs preset"""
        cmds = self.PRESETS[key]
        for x in cmds:
            x.runCmd()

    def add(self, type, type_id):
        """Add command"""
        if type == 'layer':  # add layer case
            if self.type_id_numeric:
                for x in self.SELECTED:
                    x.addLayerI(type_id)
            else:
                for x in self.SELECTED:
                    x.addLayer(type_id)
        elif type == 'stage':  # add stage case
            for x in self.SELECTED:
                x.addStage(type_id)
        else:
            raise ParsingException(self.txt, 'command "Add" not supported for type {}'.format(type))

    def remove(self, type, type_id):
        """Remove command"""
        if type == 'layer':  # add layer case
            for x in self.SELECTED:
                x.removeLayer(type_id)
        elif type == 'stage':  # add stage case
            if type_id == 0:
                type_id = 1  # assume 1
            for x in self.SELECTED:
                for i in range(type_id):
                    x.removeStage()
        else:
            raise ParsingException(self.txt, 'command "Remove" not supported for type {}'.format(type))

    def __str__(self):
        return "{} {}:{} for {} in file {} model {}".format(self.cmd,
                                                            self.key, self.value, self.name, self.file,
                                                            self.model)


def run_commands(commandlist):
    for cmd in commandlist:
        try:
            cmd.runCmd()
        except ValueError as e:
            print(e)


def load_commandfile(filename):
    if not os.path.exists(filename):
        print("No such file {}".format(filename))
        exit(2)
    f = open(filename, "r")
    lines = f.readlines()
    commands = []
    preset_begin = False
    preset = []
    for line in lines:
        if line[0].isalpha():
            i = line.find("#")
            if i != -1:
                line = line[0:i]
            if preset_begin:
                preset.append(Command(line))
            else:
                commands.append(Command(line))
        elif line[0] == '[':  # preset
            i = line.find(']')
            if i != -1:
                if i > 1:
                    preset_begin = True
                    preset = []
                    name = line[1:i]
                    Command.PRESETS[name] = preset
                else:
                    preset_begin = False
    return commands


def getFiles(filename):
    directory, name = os.path.split(filename)
    if not directory:
        directory = "."
    files = []
    for file in os.listdir(directory):
        if fnmatch.fnmatch(file, name):
            files.append(os.path.join(directory, file))
    return files


def openFiles(filenames, files):
    # remove any names that are already open
    opened = []
    openedNames = []
    for i in range(len(files)):
        openedFile = files[i]
        if not openedFile.name in filenames:
            openedFile.close()
        else:
            opened.append(openedFile)
            openedNames.append(openedFile.name)
    # open any that aren't opened
    for f in filenames:
        if not f in openedNames:
            brres = Brres(f)
            opened.append(brres)
    return opened
