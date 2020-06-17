# ---------------------------------------------------------------------------
# Command class and functions
# ---------------------------------------------------------------------------
import fnmatch
import os

from abmatt.binfile import UnpackingError
from abmatt.brres import Brres
from abmatt.layer import Layer
from abmatt.matching import validInt, findAll
from abmatt.material import Material
from abmatt.mdl0 import Mdl0
from abmatt.shader import Shader, Stage
from abmatt.pat0 import Pat0
from abmatt.srt0 import Srt0, SRTMatAnim, SRTTexAnim


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
    COMMANDS = ["preset", "set", "add", "remove", "info", "select", "save"]
    SELECTED = []  # selection list
    SELECT_TYPE = None  # current selection list type
    SELECT_ID = None  # current selection id
    SELECT_ID_NUMERIC = False  # current id numeric
    DESTINATION = None
    OVERWRITE = False
    ACTIVE_FILES = []
    FILES_MARKED = False  # files marked as modified
    MODELS = []
    MATERIALS = []
    PRESETS = {}

    TYPE_SETTING_MAP = {
        "material": Material.SETTINGS,
        "layer": Layer.SETTINGS,
        "shader": Shader.SETTINGS,
        "stage": Stage.SETTINGS,
        "mdl0": Mdl0.SETTINGS,
        "brres": Brres.SETTINGS,
        "srt0": SRTMatAnim.SETTINGS,
        "srt0layer": SRTTexAnim.SETTINGS,
        "pat0": Pat0.SETTINGS
    }

    def __init__(self, text):
        """ parses the text as a command """
        self.has_type_id = self.hasSelection = False
        self.name = self.key = None
        self.txt = text.strip('\r\n')
        x = [x.strip() for x in text.split()]
        if not x:
            raise ParsingException(self.txt, 'No Command detected')
        is_preset = self.setCmd(x.pop(0).lower())
        if not x:
            if self.cmd != 'info' and self.cmd != 'save':
                raise ParsingException(self.txt, 'Not enough parameters')
            else:
                self.type = None
                self.overwrite = False
                self.destination = self.file = None
                return
        if self.setType(x[0]):
            x.pop(0)
        if self.cmd == 'select':
            self.setSelection(x)
            return
        elif self.cmd == 'save':
            self.setSave(x)
            return
        for_index = -1
        for i in range(len(x)):
            if x[i].lower() == 'for':
                for_index = i
                break
        if for_index >= 0:
            self.setSelection(x[for_index + 1:])
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
            if self.key != 'name':
                self.value = value.lower()
            else:
                self.value = value
        elif len(x):
            if self.cmd != 'info':
                print("Unknown parameter(s) {}".format(x))
            else:
                self.key = x[0].lower()
                if self.key == 'keys':
                    return
        if self.key and self.type and self.key not in self.TYPE_SETTING_MAP[self.type]:
            raise ParsingException(self.txt, "Unknown Key {} for {}, possible keys:\n\t{}".format(self.key, self.type,
                                                                                                  self.TYPE_SETTING_MAP[
                                                                                                      self.type]))

    def setSave(self, params):
        saveAs = False
        self.overwrite = False
        self.destination = None
        self.file = None
        for x in params:
            if x == 'as':
                saveAs = True
            elif x == 'overwrite':
                self.overwrite = True
            elif saveAs and not self.destination:
                self.destination = x
            elif not self.file:
                self.file = x
                self.hasSelection = True

    def setType(self, val):
        """Returns true if the type is set by val (consumed)"""
        if self.cmd == 'preset':
            self.type = 'material'
            return False
        elif self.cmd == 'select' or self.cmd == 'save':
            return False
        i = val.find(':')
        type_id = None
        if i >= 0:
            type_id = val[i + 1:]
            val = val[:i]
        val = val.lower()
        if val in ('material', 'shader', 'srt0', 'pat0'):
            if self.cmd == 'add' or self.cmd == 'remove':
                raise ParsingException(self.txt, 'Add/Remove not supported for {}.'.format(val))
        elif val in ('layer', 'srt0layer', 'pat0layer', 'stage'):
            self.has_type_id = True
            try:
                self.type_id = validInt(type_id, 0, 16) if type_id else None
                self.type_id_numeric = True
            except ValueError:
                self.type_id = type_id
                self.type_id_numeric = False
            # elif 'srt0' in val:
        #     self.type = 'srt0'
        elif val == 'mdl0' or val == 'brres':
            if type_id:
                self.has_type_id = True
                self.type_id_numeric = False
                self.type_id = type_id
            else:
                self.type_id = '*'
        else:
            self.type = None
            return False
        self.type = val
        return True

    def setSelection(self, li):
        """ takes a list and parses selection """
        if not li:
            print("No selection given")
            self.hasSelection = False
            return False
        self.hasSelection = True
        self.name = li[0]
        self.model = self.file = x = None
        if len(li) > 1:
            if li[1] != 'in':
                raise ParsingException(self.txt, 'Expected "in"')
            li = li[2:]
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
                    elif not self.file:
                        self.file = li[i]
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
        Command.FILES_MARKED = False
        return True

    def updateSelection(self):
        """ updates container items """
        if self.file:
            if not self.updateFile(self.file):
                return False
        # Models
        if self.model or not self.MODELS:
            for x in self.ACTIVE_FILES:
                Command.MODELS.extend(x.getModelsByName(self.model))
        # Materials
        Command.MATERIALS = []  # reset materials
        for x in self.MODELS:
            Command.MATERIALS.extend(x.getMaterialsByName(self.name))
        if not Command.MATERIALS:
            print('No matches found for {}'.format(self.name))
        Command.SELECT_TYPE = None  # reset selection
        return True

    @staticmethod
    def detectType(key):
        map = Command.TYPE_SETTING_MAP
        previous = Command.SELECT_TYPE  # try the previous type settings first
        isKeys = key == 'keys'
        if previous and (isKeys or key in map[previous]):
            return previous
        if isKeys:
            return 'material'
        for x in map:
            if x != previous and key in map[x]:
                return x

    def updateTypeID(self, type_has_changed):
        """Updates SELECT_ID, SELECT_ID_NUMERIC"""
        has_changed = False
        if not self.has_type_id:
            Command.SELECT_ID = None  # reset
        elif self.type_id:  # explicit
            if self.SELECT_ID_NUMERIC != self.type_id_numeric or self.type_id != self.SELECT_ID:
                Command.SELECT_ID = self.type_id
                Command.SELECT_ID_NUMERIC = self.type_id_numeric
                has_changed = True
        else:  # implicit
            if type_has_changed or not Command.SELECT_ID:
                Command.SELECT_ID = 0  # use defaults
                Command.SELECT_ID_NUMERIC = True
                has_changed = True
            # else continue using current select_id
        return has_changed

    def updateType(self):
        """Updates SELECT_TYPE, SELECT_ID, SELECT_ID_NUMERIC
            returns true if modified
        """
        current = self.SELECT_TYPE
        if self.cmd == 'add' or self.cmd == 'remove':  # use parents as selection
            Command.SELECT_TYPE = 'shader' if self.type == 'stage' else 'material'
        else:
            if self.type:
                Command.SELECT_TYPE = self.type
            else:  # auto detect
                if self.key:
                    Command.SELECT_TYPE = self.detectType(self.key)  # possibly ambiguous for stages/layers?
                    if not Command.SELECT_TYPE:
                        raise ParsingException(self.txt, 'Unknown key {}!'.format(self.key))
                    if self.SELECT_TYPE == 'layer' or self.SELECT_TYPE == 'stage':
                        self.has_type_id = True
                        self.type_id = None
                        self.type_id_numeric = False
                elif not self.SELECT_TYPE:
                    Command.SELECT_TYPE = 'material'
        has_changed = current != self.SELECT_TYPE
        return self.updateTypeID(has_changed) or has_changed

    def updateTypeSelection(self):
        """ Updates the current selection by the type"""
        if self.updateType():
            type = Command.SELECT_TYPE
            if type == 'material':
                Command.SELECTED = self.MATERIALS
            elif type == 'layer':
                if self.SELECT_ID_NUMERIC:
                    Command.SELECTED = [x.getLayerI(self.SELECT_ID) for x in self.MATERIALS]
                else:
                    Command.SELECTED = []
                    for x in self.MATERIALS:
                        Command.SELECTED.extend(x.getLayers(self.SELECT_ID))
                    if not Command.SELECTED:  # Forcibly adding case if no selected found
                        # possible todo... make this optional?
                        Command.SELECTED = [x.forceAdd(self.SELECT_ID) for x in self.MATERIALS]

            # elif self.type == 'srt0':
            #     pass # todo
            elif type == 'shader' or type == 'stage':
                shaders = getShadersFromMaterials(self.MATERIALS, self.MODELS)
                if type == 'shader':
                    Command.SELECTED = shaders
                else:
                    Command.SELECTED = []
                    for x in shaders:
                        Command.SELECTED.append(x.getStage(self.SELECT_ID))
            elif type == 'mdl0':
                    Command.SELECTED = findAll(self.SELECT_ID, self.MODELS)
            elif type == 'brres':
                    Command.SELECTED = findAll(self.SELECT_ID, self.ACTIVE_FILES)
            elif 'srt0' in type:
                pass # todo
            elif 'pat0' in type:
                pass # todo

    @staticmethod
    def markModified():
        if not Command.FILES_MARKED:
            for x in Command.ACTIVE_FILES:
                x.isModified = True
            Command.FILES_MARKED = True

    def runCmd(self):
        if self.hasSelection:
            if not self.updateSelection():
                return False
            elif self.cmd == 'select':
                return True
        elif not self.MATERIALS and self.cmd == 'info':
            if self.key == 'keys':
                ctype = self.type if self.type else self.SELECT_TYPE
                self.info_keys(ctype)
                return True
            self.file = self.model = self.name = None
            self.updateSelection()
        if self.cmd == 'preset':
            return self.runPreset(self.key)
        if not self.ACTIVE_FILES:
            raise ParsingException(self.txt, 'No file detected!')
        if self.cmd == 'save':
            self.run_save()
            return True
        self.updateTypeSelection()
        if not self.SELECTED:
            print("No items found in selection for '{}'".format(self.txt))
            return False
        else:
            if self.cmd == 'set':
                self.markModified()
                for x in self.SELECTED:
                    x[self.key] = self.value
            elif self.cmd == 'info':
                if self.key == 'keys':
                    self.info_keys(self.SELECT_TYPE)
                else:
                    for x in self.SELECTED:
                        x.info(self.key)
                # for y in self.ACTIVE_FILES:
                #     print(y.name)
            elif self.cmd == 'add':
                self.markModified()
                self.add(self.SELECT_TYPE, self.SELECT_ID)
            elif self.cmd == 'remove':
                self.markModified()
                self.remove(self.SELECT_TYPE, self.SELECT_ID)
        return True

    def info_keys(self, type):
        if not type:
            for x in self.TYPE_SETTING_MAP:
                print('>{} keys: {}\n'.format(x, self.TYPE_SETTING_MAP[x]))
        else:
            print('>{} keys: {}'.format(type, self.TYPE_SETTING_MAP[type]))

    def run_save(self):
        for x in self.ACTIVE_FILES:
            x.save(self.destination, self.overwrite)

    def runPreset(self, key):
        """Runs preset"""
        cmds = self.PRESETS[key]
        for x in cmds:
            x.runCmd()

    def add(self, type, type_id):
        """Add command"""
        if self.SELECT_ID_NUMERIC and type_id == 0:
            type_id = 1
        if type == 'material':  # add layer case
            if self.SELECT_ID_NUMERIC:
                for x in self.SELECTED:
                    for i in range(type_id):
                        x.addEmptyLayer()
            else:
                for x in self.SELECTED:
                    x.addLayer(type_id)
        elif type == 'shader':  # add stage case
            for x in self.SELECTED:
                x.addStage(type_id)
        else:
            raise ParsingException(self.txt, 'command "Add" not supported for type {}'.format(type))

    def remove(self, type, type_id):
        """Remove command"""
        if self.SELECT_ID_NUMERIC and type_id == 0:
            type_id = 1
        if type == 'material':  # remove layer case
            if self.SELECT_ID_NUMERIC:
                for x in self.SELECTED:
                    for i in range(type_id):
                        x.removeLayerI()
            else:
                for x in self.SELECTED:
                    x.removeLayer(type_id)
        elif type == 'shader':  # remove stage case
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
        # try:
            cmd.runCmd()
        # except ValueError as e:
        #     print(e)


def load_commandfile(filename):
    if not os.path.exists(filename):
        print("No such file {}".format(filename))
        exit(2)
    f = open(filename, "r")
    lines = f.readlines()
    commands = []
    preset_begin = False
    preset = []
    name = None
    for line in lines:
        if line[0].isalpha():
            i = line.find("#")
            if i != -1:
                line = line[0:i]
            if preset_begin:
                try:
                    preset.append(Command(line))
                except ParsingException as e:
                    print('Preset {} : {}'.format(name, e))
                    Command.PRESETS[name] = None
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
        if f not in openedNames:
            try:
                brres = Brres(f)
                opened.append(brres)
            except UnpackingError as e:
                print(e)
    return opened
