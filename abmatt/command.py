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
from abmatt.pat0 import Pat0, Pat0MatAnimation
from abmatt.srt0 import Srt0, SRTMatAnim, SRTTexAnim
from abmatt.autofix import AUTO_FIXER


class ParsingException(Exception):
    def __init__(self, txt, message=''):
        super(ParsingException, self).__init__("ERROR parsing: '" + txt + "' " + message)


class SaveError(Exception):
    def __init__(self, message=''):
        super(SaveError, self).__init__(message)


class NoSuchFile(Exception):
    def __init__(self, path):
        super(NoSuchFile, self).__init__('No such file "{}"'.format(path))


class PasteError(Exception):
    def __init__(self, message=''):
        super(PasteError, self).__init__(message)


def getShadersFromMaterials(materials, for_modification=True):
    """Gets unique shaders from material list, where materials may come from different models,
        may have to detach if shared with material not in list
    """
    shaders = []
    models_checked = []
    for x in materials:
        mdl = x.parent
        if mdl not in models_checked:
            models_checked.append(mdl)
            shaders.extend(mdl.getShaders(materials, for_modification))
    return shaders


def getParents(group):
    parents = []
    for x in group:
        if x.parent not in parents:
            parents.append(x.parent)
    return parents


class Command:
    COMMANDS = ["preset", "set", "add", "remove", "info", "select", "save", "copy", "paste"]
    SELECTED = []  # selection list
    SELECT_TYPE = None  # current selection list type
    SELECT_ID = None  # current selection id
    SELECT_ID_NUMERIC = False  # current id numeric
    DESTINATION = None
    OVERWRITE = False
    ACTIVE_FILES = []
    FILES_MARKED = set()  # files marked as modified
    MODELS = []
    MATERIALS = []
    PRESETS = {}
    CLIPBOARD = None
    CLIPTYPE = None

    TYPE_SETTING_MAP = {
        "material": Material.SETTINGS,
        "layer": Layer.SETTINGS,
        "shader": Shader.SETTINGS,
        "stage": Stage.SETTINGS,
        "mdl0": Mdl0.SETTINGS,
        "brres": Brres.SETTINGS,
        "srt0": SRTMatAnim.SETTINGS,
        "srt0layer": SRTTexAnim.SETTINGS,
        "pat0": Pat0MatAnimation.SETTINGS
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
                raise ParsingException(self.txt, "Unknown parameter(s) {}".format(x))
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
        self.file = self.model = None
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
        if val in ('material', 'shader'):
            if self.cmd == 'add' or self.cmd == 'remove':
                raise ParsingException(self.txt, 'Add/Remove not supported for {}.'.format(val))
        elif val in ('layer', 'srt0layer', 'stage'):
            self.has_type_id = True
            try:
                self.type_id = validInt(type_id, 0, 16) if type_id else None
                self.type_id_numeric = True
            except ValueError:
                self.type_id = type_id
                self.type_id_numeric = False
            # elif 'srt0' in val:
        #     self.type = 'srt0'
        elif val in ('mdl0', 'brres'):
            if self.cmd == 'add' or self.cmd == 'remove':
                raise ParsingException(self.txt, 'Add/Remove not supported for {}.'.format(val))
            if type_id:
                self.has_type_id = True
                self.type_id_numeric = False
                self.type_id = type_id
            else:
                self.type_id = '*'
        elif val in ('srt0', 'pat0'):
            pass
        else:
            self.type = None
            return False
        self.type = val
        return True

    def setSelection(self, li):
        """ takes a list and parses selection """
        if not li:
            raise ParsingException("No selection given")
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
                    x = li[i].lower()
                    if x == 'file':
                        i += 1
                        self.file = li[i]  # possible exception
                    elif x == 'model':
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

    # ----------------------------  FILE STUFF ---------------------------------------------------------
    @staticmethod
    def updateFile(filename):
        files = Command.getFiles(filename)
        if Command.DESTINATION:  # check for multiple files with single destination
            outside_active = True
            for x in Command.ACTIVE_FILES:
                if files[0] == x.name:
                    outside_active = False
                    break
            if len(files) > 1 or Command.ACTIVE_FILES and outside_active:
                raise SaveError('Multiple files for single destination')
        Command.ACTIVE_FILES = Command.openFiles(files, Command.ACTIVE_FILES)
        Command.MODELS = []  # clear models

    @staticmethod
    def openFiles(filenames, files):
        # remove any names that are already open
        opened = []
        openedNames = []
        for i in range(len(files)):
            openedFile = files[i]
            if not openedFile.name in filenames:
                openedFile.close()
                if openedFile in Command.FILES_MARKED:
                    Command.FILES_MARKED.remove(openedFile)
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
                    AUTO_FIXER.notify(e, 1)
        return opened

    @staticmethod
    def load_commandfile(filename):
        files = Command.getFiles(filename)
        commands = []
        with open(files[0], "r") as f:
            lines = f.readlines()
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
                            AUTO_FIXER.notify('Preset {} : {}'.format(name, e), 1)
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

    @staticmethod
    def getFiles(filename):
        directory, name = os.path.split(filename)
        if not directory:
            directory = "."
        files = []
        for file in os.listdir(directory):
            if fnmatch.fnmatch(file, name):
                files.append(os.path.join(directory, file))
        if not files:
            raise NoSuchFile(filename)
        return files

    # ------------------------------------  UPDATING TYPE/SELECTION ------------------------------------------------
    def updateSelection(self):
        """ updates container items """
        if self.file:
            self.updateFile(self.file)
        # Models
        if self.model or not self.MODELS:
            for x in self.ACTIVE_FILES:
                Command.MODELS.extend(x.getModelsByName(self.model))
        # Materials
        Command.MATERIALS = []  # reset materials
        for x in self.MODELS:
            Command.MATERIALS.extend(x.getMaterialsByName(self.name))
        if not Command.MATERIALS:
            AUTO_FIXER.notify('No matches found for {}'.format(self.name), 4)
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
        elif self.type_id is not None:  # explicit
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
        if self.cmd == 'add' or self.cmd == 'remove':
            # use parents as selection, except (srt0, pat0)
            if self.type == 'stage':
                Command.SELECT_TYPE = 'shader'
            elif self.type == 'layer':
                Command.SELECT_TYPE = 'material'
            elif self.type == 'srt0layer':
                Command.SELECT_TYPE = 'srt0'
            elif self.type == 'pat0layer':
                Command.SELECT_TYPE = 'pat0'
            elif self.type in ('srt0', 'pat0'):
                Command.SELECT_TYPE = 'material'
        else:
            if self.type:
                Command.SELECT_TYPE = self.type
            else:  # auto detect
                if self.key:
                    Command.SELECT_TYPE = self.detectType(self.key)  # possibly ambiguous for stages/layers?
                    if not Command.SELECT_TYPE:
                        raise ParsingException(self.txt, 'Unknown key {}!'.format(self.key))
                    if self.SELECT_TYPE in ('layer', 'stage', 'srt0layer'):
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
                        layers = findAll(self.SELECT_ID, x.layers)
                        if layers:
                            Command.SELECTED.extend(layers)
                    # if not Command.SELECTED:  # Forcibly adding case if no selected found
                    #     # possible todo... make this optional?
                    #     Command.SELECTED = [x.forceAdd(self.SELECT_ID) for x in self.MATERIALS]

            elif type == 'shader' or type == 'stage':
                shaders = getShadersFromMaterials(self.MATERIALS)
                if type == 'shader':
                    Command.SELECTED = shaders
                else:
                    if self.SELECT_ID == '*':
                        Command.SELECTED = []
                        for x in shaders:
                            Command.SELECTED.extend(x.stages)
                    else:
                        Command.SELECTED = [x.getStage(self.SELECT_ID) for x in shaders]
            elif type == 'mdl0':
                Command.SELECTED = findAll(self.SELECT_ID, getParents(self.MATERIALS))
            elif type == 'brres':
                Command.SELECTED = findAll(self.SELECT_ID, getParents(getParents(self.MATERIALS)))
            elif 'srt0' in type:
                srts = [x.srt0 for x in self.MATERIALS if x.srt0]
                if 'layer' in type:
                    Command.SELECTED = []
                    if self.SELECT_ID_NUMERIC:
                        for x in srts:
                            anim = x.getTexAnimationByID(self.SELECT_ID)
                            if anim:
                                Command.SELECTED.append(anim)
                    else:
                        for x in srts:
                            anim = findAll(self.SELECT_ID, x.tex_animations)
                            if anim:
                                Command.SELECTED.extend(anim)
                else:  # material animation
                    Command.SELECTED = srts
            elif 'pat0' in type:
                Command.SELECTED = [x.pat0 for x in self.MATERIALS if x.pat0]

    @staticmethod
    def markModified():
        marked = Command.FILES_MARKED
        for x in Command.MATERIALS:
            f = x.parent.parent
            if f not in marked:
                f.isModified = True
                Command.FILES_MARKED.add(f)

    # ---------------------------------------------- RUN CMD ---------------------------------------------------
    @staticmethod
    def run_commands(commandlist):
        try:
            for cmd in commandlist:
                cmd.runCmd()
        except ValueError as e:
            AUTO_FIXER.notify(e, 1)
        except SaveError as e:
            AUTO_FIXER.notify(e, 1)

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
            AUTO_FIXER.notify("No items found in selection for '{}'".format(self.txt), 3)
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
            elif self.cmd == 'copy':
                self.run_copy(self.SELECT_TYPE)
            elif self.cmd == 'paste':
                self.run_paste(self.SELECT_TYPE)
        return True

    # -------------------------------------------- COPY/PASTE -----------------------------------------------
    #   Items implementing clipboard must support the methods:
    #       .clip(clipboard)
    #       .clip_find(clipboard)
    #       .paste(item)
    def run_copy(self, select_type):
        Command.CLIPBOARD = {}
        for x in self.SELECTED:
            x.clip(Command.CLIPBOARD)
        Command.CLIPTYPE = select_type

    def run_paste(self, select_type):
        clip = self.CLIPBOARD
        selected = self.SELECTED
        if not clip:
            raise PasteError('No items in clipboard.')
        # check for compatible types
        if select_type != self.CLIPTYPE:
            raise PasteError('Mismatched clipboard types (has {})'.format(self.CLIPTYPE))
        paste_count = 0
        if len(clip) == 1:
            item = clip[clip.keys()[0]]
            for x in selected:
                x.paste(item)
                paste_count += 1
        else:
            for x in selected:
                to_paste = x.clip_find(clip)
                if to_paste:
                    x.paste(to_paste)
                    paste_count += 1
        if paste_count == 0:
            raise PasteError('No matches found in clipboard.')
        return paste_count

    def info_keys(self, type):
        if not type:
            for x in self.TYPE_SETTING_MAP:
                print('>{} keys: {}\n'.format(x, self.TYPE_SETTING_MAP[x]))
        else:
            print('>{} keys: {}'.format(type, self.TYPE_SETTING_MAP[type]))

    def run_save(self):
        files_to_save = findAll(self.file, self.ACTIVE_FILES)
        if len(files_to_save) > 1 and self.destination is not None:
            raise SaveError('Detected {} files and only one destination "{}"'.format(len(files_to_save),
                                                                                     self.destination))
        else:
            for x in files_to_save:
                if not x.save(self.destination, self.overwrite):
                    raise SaveError('File already Exists!')

    def runPreset(self, key):
        """Runs preset"""
        cmds = self.PRESETS[key]
        for x in cmds:
            x.runCmd()

    def add(self, type, type_id):
        """Add command"""
        if self.SELECT_ID_NUMERIC and type_id == 0:
            type_id = 1
        if type == 'material':
            if self.type == 'srt0':
                for x in self.SELECTED:
                    x.add_srt0()
            elif self.type == 'pat0':
                for x in self.SELECTED:
                    x.add_pat0()
            else:  # layers
                if self.SELECT_ID_NUMERIC:
                    for x in self.SELECTED:
                        for i in range(type_id):
                            x.addEmptyLayer()
                else:
                    for x in self.SELECTED:
                        x.addLayer(type_id)
        elif type == 'shader':  # add stage case
            for x in self.SELECTED:
                for i in range(type_id):
                    x.addStage()
        elif type == 'srt0':  # add srt0 layer
            if self.SELECT_ID_NUMERIC:
                for x in self.SELECTED:
                    for i in range(type_id):
                        x.addLayer()
            else:
                for x in self.SELECTED:
                    x.addLayerByName(type_id)
        else:
            raise ParsingException(self.txt, 'command "Add" not supported for type {}'.format(type))

    def remove(self, type, type_id):
        """Remove command"""
        if self.SELECT_ID_NUMERIC and type_id == 0:
            type_id = 1
        if type == 'material':
            if self.type == 'srt0':
                for x in self.SELECTED:
                    x.remove_srt0()
            elif self.type == 'pat0':
                for x in self.SELECTED:
                    x.remove_pat0()
            else:  # remove layer case
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
        elif type == 'srt0':  # remove srt0 layer
            if self.SELECT_ID_NUMERIC:
                for x in self.SELECTED:
                    for i in range(type_id):
                        x.removeLayer()
            else:
                for x in self.SELECTED:
                    x.removeLayerByName(type_id)
        else:
            raise ParsingException(self.txt, 'command "Remove" not supported for type {}'.format(type))

    def __str__(self):
        return "{} {}:{} for {} in file {} model {}".format(self.cmd,
                                                            self.key, self.value, self.name, self.file,
                                                            self.model)
