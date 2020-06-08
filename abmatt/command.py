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
    COMMANDS = ["set", "add", "remove", "info", "select"]
    SELECTED = []  # selection list
    SELECT_TYPE = None  # current selection list type
    DESTINATION = None
    OVERWRITE = False
    ACTIVE_FILES = []
    MODELS = []
    MATERIALS = []

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
        x = [x.strip() for x in text.split()]
        if not x:
            raise ParsingException(self.txt, 'No Command detected')
        self.setCmd(x.pop(0).lower())
        if not x:
            raise ParsingException(self.txt, 'Not enough parameters')
        self.setType(x.pop(0).lower())
        if 'for' in x:
            i = x.index('for')
            self.setSelection(x[i:])
            x = x[0:i]
        if self.cmd == 'set':
            if not x:
                raise ParsingException(self.txt, 'Not enough parameters')
            if ':' not in x[0]:
                raise ParsingException(self.txt, 'Set requires key:value pair')
            self.key, self.value = x[0].split(':')
            self.key = self.key.lower()
        elif len(x):
            if self.cmd != 'info':
                print("Unknown parameter(s) {}".format(x))
            else:
                self.key = x[0].lower()
        if self.key and not self.key in self.TYPE_SETTING_MAP[self.type]:
            raise ParsingException(self.txt, "Unknown Key {} for {}".format(self.key, self.type))

    def setType(self, val):
        self.type_id = 0
        if val == 'material' or val == 'shader':
            if self.cmd == 'add' or self.cmd == 'remove':
                raise ParsingException(self.txt, 'Add/Remove not supported for materials and shaders.')
            self.type = val
            return True
        i = val.find(':')
        if i > 0 and len(val) > i + 1:
            self.type_id = val[i + 1:]
        if 'layer' in val:
            self.type = 'layer'
        elif 'stage' in val:
            self.type = 'stage'
            if self.type_id:
                self.type_id = validInt(self.type_id, 0, 15)
        # elif 'srt0' in val:
        #     self.type = 'srt0'
        else:
            raise ParsingException(self.txt, 'Invalid type {}'.format(val))

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

    @staticmethod
    def updateFile(filename):
        files = getFiles(filename)
        if not files:  # could possibly ignore error here for wildcard patterns?
            print("The file '{}' does not exist".format(filename))
            return False
        if Command.DESTINATION:     # check for multiple files with single destination
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
            Command.MATERIALS = x.getMaterialsByName(self.name)
        Command.SELECT_TYPE = None  # reset selection
        return True

    def updateType(self):
        """ Updates the current selection by the type/cmd"""
        if self.cmd == 'add' or self.cmd == 'remove':  # use parents as selection
            type = 'material' if self.type == 'layer' else 'shader'
        else:
            type = self.type
        if type != self.SELECT_TYPE:
            if type == 'material':
                Command.SELECTED = self.MATERIALS
            elif type == 'layer':
                Command.SELECTED = []
                for x in self.MATERIALS:
                    Command.SELECTED.append(x.getLayer(self.type_id))
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

    def add(self, type, type_id):
        """Add command"""
        if type == 'layer':  # add layer case
            for x in self.SELECTED:
                x.addLayer(type_id)
        elif type == 'stage':  # add stage case
            if type_id == 0:
                type_id = 1  # assume 1
            for x in self.SELECTED:
                for i in range(type_id):
                    x.addStage()
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
    for line in lines:
        if line[0].isalpha():
            i = line.find("#")
            if i != -1:
                line = line[0:i]
            commands.append(Command(line))
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
