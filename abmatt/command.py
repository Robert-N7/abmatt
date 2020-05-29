# ---------------------------------------------------------------------------
# Command class and functions
# ---------------------------------------------------------------------------
import os
import re
import sys
import fnmatch
from matching import *
from brres import Brres
from material import Material
from mdl0.layer import Layer
from mdl0.shader import Shader, Stage
from srt0 import Srt0


class ParsingException(Exception):
    def __init__(self, txt, message=''):
        super(ParsingException, self).__init__("Error parsing: '" + txt + "'' " + message)


def getShadersFromMaterials(materials, models):
    """Gets unique shaders from material list, where materials may come from different models,
        may have to detach if shared with material not in list
    """
    pass    # todo


class Command:
    COMMANDS = ["set", "add", "remove", "info", "select"]
    SELECTED = []  # selection list
    SELECT_TYPE = None # current selection list type
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
        ''' parses the text as a command '''
        self.hasSelection = False
        self.name = self.key = None
        self.txt = text
        x = self.txt.split()
        if len(x) < 2:
            raise ParsingException(self.txt, 'Not enough parameters')
        self.setCmd(x.pop(0).lower())
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
        self.typenum = 0
        if val == 'material' or val == 'shader':
            self.type = val
            return True
        r = re.match('.*?([0-9]+)$', val)
        if r != None:
            self.typenum = int(r.group(1))
        if 'layer' in val:
            self.type = 'layer'
        elif 'stage' in val:
            self.type = 'stage'
        elif 'srt0' in val:
            self.type = 'srt0'
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
        self.name = self.model = self.file = x = None
        if len(li) > 2:
            if li[2] != 'in':
                raise ParsingException(self.txt, 'Expected "in"')
            li = li [3:]
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
            raise ValueError("Unknown command '{}'".format(val))
        else:
            self.cmd = val

    def updateSelection(self):
        """ updates container items """
        if self.file:
            files = getFiles(self.file)
            if not files:  # could possibly ignore error here for wildcard patterns?
                print("The file '{}' does not exist".format(self.file))
                return False
            elif self.DESTINATION and len(files) > 1 or self.ACTIVE_FILES and not files[0] in self.ACTIVE_FILES:
                print("Error: Multiple files for single destination!")
                print("Specify single file and destination, or no destination with overwrite option.")
                return False
            else:
                self.ACTIVE_FILES = openFiles(files, self.ACTIVE_FILES)
                self.MODELS = []  # clear models
        # Models
        if self.model or not self.MODELS:
            self.MATERIALS = []  # reset materials
            for x in self.ACTIVE_FILES:
                self.MODELS.extend(x.getModelsByName(self.model))
        # Materials
        for x in self.MODELS:
            self.MATERIALS = x.getMaterialsByName(self.name)
        self.SELECT_TYPE = None # reset selection
        return True

    def updateType(self):
        """ Updates the current selection"""
        if self.type != self.SELECT_TYPE:
            if self.type == 'material' or self.cmd != 'set' and self.cmd != 'info': # use materials as selection
                self.SELECTED = self.MATERIALS
            else:
                self.SELECTED = []
                if self.type == 'layer':
                    for x in self.MATERIALS:
                        self.SELECTED.append(x.getLayer(self.typenum))
                elif self.type == 'srt0':
                    pass # todo
                else:
                    shaders = getShadersFromMaterials(self.MATERIALS, self.MODELS)
                    if self.type == 'stage':
                        for x in shaders:
                            self.SELECTED.append(x.getStage(self.typenum))
                    else:
                        self.SELECTED = shaders

    def runCmd(self):
        if self.hasSelection:
            if not self.updateSelection():
                sys.exit(1)
        if not self.SELECTED:
            print("No items found in selection for '{}'".format(self.txt))
        else:
            if self.cmd == 'set':
                for x in self.SELECTED:
                    x.set(self.type, )

    def __str__(self):
        return "{} {}:{} for {} in file {} model {}".format(self.cmd,
                                                                        self.key, self.value, self.name, self.file,
                                                                        self.model)


def run_commands(commandlist, destination, overwrite):
    files = {}
    for cmd in commandlist:
        if cmd.filename:
            filenames = getFiles(cmd.filename)
            closeFiles(filenames, files, destination, overwrite)
            openFiles(filenames, files)
        for index in files:
            files[index].parseCommand(cmd)
    closeFiles(None, files, destination, overwrite)


def load_commandfile(filename):
    if not os.path.exists(filename):
        print("No such file {}".format(filename))
        exit(2)
    f = open(filename, "r")
    lines = f.readlines()
    # regex = re.compile("(?P<cmd>\w+)\s*(for\s+(?P<item>\S+)|(?P<key>\w+)?(\s*:(?P<value>\w+))?(\s+for\s+(?P<item2>\S+))?)(\s+in(\s+file\s+(?P<fname>\S+))?(\s+model\s+(?P<modelname>\S+))?(\s+material\s+(?P<matname>\S+))?)?$")
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
            if __debug__:
                print("Opening file {}".format(f))
            brres = Brres(f)
            opened.append(brres)
    return opened
