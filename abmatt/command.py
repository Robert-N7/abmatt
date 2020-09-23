# ---------------------------------------------------------------------------
# Command class and functions
# ---------------------------------------------------------------------------
import fnmatch
import os

from abmatt.brres import Brres
from abmatt.brres.lib.autofix import AUTO_FIXER
from abmatt.brres.lib.matching import validInt, MATCHING
from abmatt.brres.mdl0 import Mdl0
from abmatt.brres.mdl0.layer import Layer
from abmatt.brres.mdl0.material import Material
from abmatt.brres.mdl0.shader import Shader, Stage
from abmatt.brres.pat0 import Pat0MatAnimation
from abmatt.brres.srt0 import SRTMatAnim, SRTTexAnim
from abmatt.brres.tex0 import Tex0, ImgConverter, EncodeError, NoImgConverterError
from abmatt.brres.lib.binfile import UnpackingError, PackingError


def convert_file_ext(path, new_ext):
    dir, name = os.path.split(path)
    base_name = os.path.splitext(name)[0]
    return os.path.join(dir, base_name + new_ext)


class ParsingException(Exception):
    def __init__(self, txt, message=''):
        super(ParsingException, self).__init__("Failed to parse: '" + txt + "' " + message)


class SaveError(Exception):
    def __init__(self, message=''):
        super(SaveError, self).__init__(message)


class NoSuchFile(Exception):
    def __init__(self, path):
        super(NoSuchFile, self).__init__('No such file "{}"'.format(path))


class MaxFileLimit(Exception):
    def __init__(self):
        super(MaxFileLimit, self).__init__('Max file limit reached')


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
    return {x.parent for x in group}


def getBrresFromMaterials(mats):
    return {m.getBrres() for m in mats}


class Command:
    COMMANDS = ["preset", "set", "add", "remove", "info", "select", "save", "copy", "paste", "convert"]
    SELECTED = []  # selection list
    SELECT_TYPE = None  # current selection list type
    SELECT_ID = None  # current selection id
    SELECT_ID_NUMERIC = False  # current id numeric
    DESTINATION = None
    OVERWRITE = False
    ACTIVE_FILES = []  # currently being used in selection
    OPEN_FILES = {}  # currently open
    FILES_MARKED = set()  # files marked as modified
    MODELS = []
    MATERIALS = []
    PRESETS = {}
    PRESETS_LOADED = False
    APP_DIR = None
    CLIPBOARD = None
    CLIPTYPE = None
    MAX_FILES_OPEN = 6
    DEBUG = False

    @staticmethod
    def set_max_brres_files(config):
        max_brres_files = config['max_brres_files']
        if max_brres_files:
            try:
                i = int(max_brres_files)
                Command.MAX_FILES_OPEN = i
            except ValueError:
                pass

    TYPE_SETTING_MAP = {
        "material": Material.SETTINGS,
        "layer": Layer.SETTINGS,
        "shader": Shader.SETTINGS,
        "stage": Stage.SETTINGS,
        "mdl0": Mdl0.SETTINGS,
        "brres": Brres.SETTINGS,
        "srt0": SRTMatAnim.SETTINGS,
        "srt0layer": SRTTexAnim.SETTINGS,
        "pat0": Pat0MatAnimation.SETTINGS,
        "tex0": Tex0.SETTINGS
    }

    def __init__(self, text):
        """ parses the text as a command """
        self.has_type_id = self.hasSelection = False
        self.name = self.key = None
        self.txt = text.strip('\r\n')
        x = [x.strip() for x in text.split()]
        if not x:
            raise ParsingException(self.txt, 'No Command detected')
        cmd = self.setCmd(x.pop(0).lower())
        if not x:
            if cmd != 'info' and cmd != 'save':
                raise ParsingException(self.txt, 'Not enough parameters')
            else:
                self.type = None
                self.overwrite = False
                self.destination = self.file = None
                return
        if cmd == 'convert':
            self.set_convert(x)
            return
        if self.setType(x[0]):
            x.pop(0)
        if cmd == 'select':
            self.setSelection(x)
            return
        elif cmd == 'save':
            self.setSave(x)
            return
        in_index = for_index = -1
        for i in range(len(x)):
            if x[i].lower() == 'for':
                for_index = i
                x[i] = 'for'
                break
            elif x[i].lower() == 'in':
                in_index = i
                x[i] = 'in'
                break
        if for_index >= 0:
            self.setSelection(x[for_index + 1:])
            x = x[0:for_index]
        elif in_index >= 0:
            self.setSelection(x[in_index:])
            x = x[0:in_index]
        if cmd == 'preset':
            if not self.PRESETS_LOADED:
                Command.PRESETS_LOADED = True
                load_presets(self.APP_DIR)
            key = x[0]
            if key not in self.PRESETS:
                raise ParsingException(self.txt, 'No such preset {}'.format(key))
            self.key = key
            return
        elif cmd == 'set':
            if not x:
                raise ParsingException(self.txt, 'Not enough parameters')
            self.set_key_val(x[0])
        elif cmd == 'add' and len(x):
            self.set_key_val(x[0])
        elif len(x):
            if cmd != 'info':
                raise ParsingException(self.txt, "Unknown parameter(s) {}".format(x))
            else:
                self.key = x[0].lower()
                if self.key == 'keys':
                    return
        if self.key and self.type and self.key not in self.TYPE_SETTING_MAP[self.type]:
            raise ParsingException(self.txt, "Unknown Key {} for {}, possible keys:\n\t{}".format(
                self.key, self.type, self.TYPE_SETTING_MAP[self.type]))

    def set_convert(self, params):
        flags = 0
        self.name = self.destination = self.model = None
        while len(params):
            param = params.pop(0)
            lower = param.lower()
            if lower == 'to':
                try:
                    self.destination = os.path.normpath(params.pop(0))
                except IndexError:
                    raise ParsingException('Expected destination after "to"')
            elif lower == 'in':
                model = self.name
                try:
                    self.name = os.path.normpath(params.pop(0))
                except IndexError:
                    raise ParsingException('Expected brres filename after keyword "in"')
            elif lower == 'no-normals':
                flags |= 1
            elif lower == 'no-colors':
                flags |= 2
            elif not self.name:
                self.name = os.path.normpath(param)
            else:
                raise ParsingException('Unknown parameter {}'.format(param))
        self.ext = None
        supported_formats = ('.dae', '.obj')
        self.is_import = False
        if self.name:
            dir, filename = os.path.split(self.name)
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in supported_formats:
                self.is_import = True
                self.ext = ext
        if self.destination and self.is_import:
            dir, filename = os.path.split(self.destination)
            split = os.path.splitext(filename)
            try:
                ext = split[1]
            except IndexError:
                ext = None
            if ext is None or ext.lower() != '.brres':
                if ext:
                    AUTO_FIXER.warn('Unsupported target extension {}, using .brres'.format(ext))
                self.destination += '.brres'
        if not self.is_import:
            if not self.destination:
                raise ParsingException('Convert requires target!')
            dir, filename = os.path.split(self.destination)
            base_name, ext = os.path.splitext(filename)
            self.ext = ext.lower()
            if self.ext not in supported_formats:
                raise ParsingException('Unsupported export format {}'.format(self.ext))
        self.flags = flags

    def set_key_val(self, keyval):
        if ':' not in keyval:
            raise ParsingException(self.txt, 'Requires key:value pair')
        key, value = keyval.split(':', 1)
        self.key = key.lower()
        if self.key != 'name':
            self.value = value.lower()
        else:
            self.value = value

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
                self.destination = os.path.normpath(x)
            elif not self.file:
                self.file = os.path.normpath(x)
                self.hasSelection = True

    def detectImportType(self, ext):
        if ext.lower() in ('dae', 'obj'):
            return 'model'

    def setType(self, val):
        """Returns true if the type is set by val (consumed)"""
        if self.cmd == 'preset':
            self.type = 'material'
            return False
        elif self.cmd in ('select', 'save'):
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
        elif val in ('layer', 'srt0layer', 'stage', 'mdl0', 'tex0'):
            self.has_type_id = True
            try:
                self.type_id = validInt(type_id, 0, 16) if type_id else None
                self.type_id_numeric = True
            except ValueError:
                self.type_id = type_id
                self.type_id_numeric = False
            # elif 'srt0' in val:
        #     self.type = 'srt0'
        elif val == 'brres':
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
        in_sel = self.model = self.file = x = None
        self.name = '*'
        if li[0] == 'for':
            li.pop(0)
        # split on 'in'
        if 'in' in li:
            in_index = li.index('in')
            in_sel = li[in_index + 1:]
            sel = li[:in_index]
        else:
            sel = li
        # set name
        if len(sel) == 1:
            self.name = sel[0]
        elif len(sel) > 1:
            raise ParsingException(self.txt, 'Unexpected param {}'.format(sel[1]))
        # parse 'in' clause
        if in_sel:
            i = 0
            try:  # to get args
                while i < len(in_sel):
                    x = in_sel[i].lower()
                    if x == 'file':
                        i += 1
                        self.file = os.path.normpath(in_sel[i])  # possible exception
                    elif x == 'model':
                        i += 1
                        self.model = in_sel[i]
                    elif not self.file:
                        self.file = os.path.normpath(in_sel[i])
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
        return self.cmd

    # ----------------------------  FILE STUFF ---------------------------------------------------------
    @staticmethod
    def updateFile(filename):
        # check in opened files
        files = MATCHING.findAll(filename, Command.OPEN_FILES.values())
        if files:
            Command.ACTIVE_FILES = files
        else:
            # try to find file path
            files = Command.getFiles(filename)
            if Command.DESTINATION:  # check for multiple files with single destination
                outside_active = True
                for x in Command.ACTIVE_FILES:
                    if files[0] == x.name:
                        outside_active = False
                        break
                if len(files) > 1 or Command.ACTIVE_FILES and outside_active:
                    raise SaveError('Multiple files for single destination')
            Command.ACTIVE_FILES = Command.openFiles(files)
        Command.MODELS = []
        Command.MATERIALS = []
        return Command.ACTIVE_FILES

    @staticmethod
    def closeFiles(file_names):
        opened = Command.OPEN_FILES
        marked = Command.FILES_MARKED
        for x in file_names:
            file = opened.pop(x)
            file.close()
            marked.remove(file)

    @staticmethod
    def auto_close(amount, exclude=[]):
        can_close = []  # modified but can close
        to_close = []  # going to close if needs closing
        excluded = []
        opened = Command.OPEN_FILES
        # first pass, mark non-modified files for closing, and appending active
        for x in opened:
            if x not in exclude:
                if not opened[x].isModified:
                    to_close.append(x)
                    amount -= 1
                else:
                    can_close.append(x)
            else:
                excluded.append(opened[x])
        if amount:
            for x in can_close:
                to_close.append(x)
                amount -= 1
                if not amount:
                    break
        Command.closeFiles(to_close)
        return excluded

    @staticmethod
    def openFiles(filenames):
        opened = Command.OPEN_FILES
        max = Command.MAX_FILES_OPEN  # max that can remain open
        if max - len(filenames) < 0:
            raise MaxFileLimit
        to_open = [f for f in filenames if f not in opened]
        total = len(to_open) + len(opened)
        if total > max:
            active = Command.auto_close(total - max, to_open)
            for x in active:
                to_open.remove(x.name)
        else:
            active = []
        # open any that aren't opened
        for f in to_open:
            # try:
            brres = Brres(f)
            opened[f] = brres
            active.append(brres)
        # except UnpackingError as e:
        #     AUTO_FIXER.error(e)
        Brres.OPEN_FILES = opened.values()
        return active

    @staticmethod
    def create_or_open(filename):
        amount = len(Command.OPEN_FILES) - Command.MAX_FILES_OPEN
        if amount > 0:
            Command.auto_close(amount, [filename])
        if os.path.exists(filename):
            files = Command.updateFile(filename)
            b = files[0] if len(files) else None
        else:
            b = Brres(filename, readFile=False)
            Command.OPEN_FILES[filename] = b
            Command.ACTIVE_FILES = [b]
            Command.MODELS = []
        return b

    @staticmethod
    def load_commandfile(filename):
        files = Command.getFiles(filename)
        commands = []
        with open(files[0], "r") as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                AUTO_FIXER.error('Not a text file {}'.format(filename))
                return
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
                            AUTO_FIXER.error('Preset {} : {}'.format(name, e), 1)
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
            Command.MODELS = []
            for x in self.ACTIVE_FILES:
                Command.MODELS.extend(x.getModelsByName(self.model))
            if self.MATERIALS:
                Command.MATERIALS = []
        # Materials
        for x in self.MODELS:
            Command.MATERIALS.extend(x.getMaterialsByName(self.name))
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
            elif self.type in ('tex0', 'mdl0'):
                Command.SELECT_TYPE = 'brres'
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
                        layers = MATCHING.findAll(self.SELECT_ID, x.layers)
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
                if self.SELECT_ID_NUMERIC:
                    brres = getBrresFromMaterials(self.MATERIALS)
                    Command.SELECTED = {x.getModelI(self.SELECT_ID) for x in brres}
                else:
                    Command.SELECTED = MATCHING.findAll(self.SELECT_ID, getParents(self.MATERIALS))
            elif type == 'brres':
                if self.cmd in ('add', 'remove'):
                    Command.SELECTED = getBrresFromMaterials(self.MATERIALS)
                else:
                    Command.SELECTED = MATCHING.findAll(self.SELECT_ID, getBrresFromMaterials(self.MATERIALS))
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
                            anim = MATCHING.findAll(self.SELECT_ID, x.tex_animations)
                            if anim:
                                Command.SELECTED.extend(anim)
                else:  # material animation
                    Command.SELECTED = srts
            elif 'pat0' in type:
                Command.SELECTED = [x.pat0 for x in self.MATERIALS if x.pat0]
            elif 'tex0' == type:
                Command.SELECTED = []
                for x in getBrresFromMaterials(self.MATERIALS):
                    Command.SELECTED.extend(MATCHING.findAll(self.SELECT_ID, x.textures))

    @staticmethod
    def markModified():
        marked = Command.FILES_MARKED
        for f in Command.ACTIVE_FILES:
            if f not in marked:
                f.isModified = True
                Command.FILES_MARKED.add(f)

    # ---------------------------------------------- RUN CMD ---------------------------------------------------
    @staticmethod
    def run_commands(commandlist):
        if Command.DEBUG:
            for cmd in commandlist:
                cmd.run_cmd()
        else:
            try:
                for cmd in commandlist:
                    cmd.run_cmd()
            except (ValueError, SaveError, PasteError, MaxFileLimit, NoSuchFile, FileNotFoundError, ParsingException,
                    OSError, UnpackingError, PackingError, NotImplementedError, NoImgConverterError) as e:
                AUTO_FIXER.error(e)
                return False
        return True

    def run_import(self, files, converted_format=None):
        mdl_extensions = ('dae', 'obj')
        tex0_extensions = ('png')
        for file in files:
            name, ext = os.path.splitext(os.path.basename(files[0]))
            ext = ext.lower()
            is_mdl = ext in mdl_extensions
            if not is_mdl:
                is_tex0 = ext in tex0_extensions
                if not is_tex0:
                    raise ParsingException(self.txt, 'ext {} not supported.'.format(ext))
            if is_mdl:
                self.import_model(file)
            else:
                tex0 = self.import_texture(file, converted_format)
                if tex0:
                    for x in self.SELECTED:
                        x.add_tex0(tex0)

    def import_model(self, file):
        try:
            self.ext = os.path.splitext(os.path.basename(file))[1].lower()
        except IndexError:
            raise ParsingException('Unknown model format {}'.format(file))
        self.name = file
        self.is_import = True
        self.flags = 0
        self.destination = None
        self.run_convert()

    def import_texture(self, file, tex_format=None):
        try:
            return ImgConverter().encode(file, tex_format)
        except EncodeError as e:
            print(e)

    def run_cmd(self):
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
        elif self.cmd == 'convert':
            return self.run_convert()
        if not self.ACTIVE_FILES:
            raise ParsingException(self.txt, 'No file detected!')
        if self.cmd == 'save':
            self.run_save()
            return True
        self.updateTypeSelection()
        if not self.SELECTED:
            AUTO_FIXER.error("No items found in selection for '{}'".format(self.txt), 3)
            return False
        if self.cmd == 'set':
            self.markModified()
            for x in self.SELECTED:
                x.set_str(self.key, self.value)
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

    def run_convert(self):
        if self.ext == '.dae':
            from abmatt.converters.convert_dae import DaeConverter2
            klass = DaeConverter2
        elif self.ext == '.obj':
            from abmatt.converters.convert_obj import ObjConverter
            klass = ObjConverter
        else:
            raise ParsingException('Unknown conversion format {}'.format(self.ext))
        active_files = self.ACTIVE_FILES
        if not self.name:
            files = [x.name for x in active_files]
        else:
            files = self.getFiles(self.name)
        if not files:
            return False
        multiple_files = False if len(files) < 2 else True
        if self.is_import:
            if not self.destination:
                if active_files and not multiple_files:
                    brres = active_files[0]
                else:
                    brres = None
            else:
                brres = self.create_or_open(self.destination)
            for file in files:
                if not brres:
                    converter = klass(self.create_or_open(convert_file_ext(file, '.brres')), file, self.flags)
                else:
                    converter = klass(brres, file, self.flags)
                base_name = os.path.splitext(os.path.basename(converter.brres.name))[0]
                model = self.model
                if model and len(model) > len(base_name) and model.startswith(base_name + '-'):
                    model = model[len(model) + 1:]
                mdl = converter.load_model(model)
        else:  # export
            dest_auto = True if multiple_files or os.path.basename(self.destination).lower() == '*' + self.ext else False
            for file in files:
                destination = self.destination if not dest_auto \
                    else os.path.join(os.path.dirname(self.destination), convert_file_ext(os.path.basename(file), self.ext))
                brres = self.create_or_open(file)
                converter = klass(brres, destination, self.flags)
                models = MATCHING.findAll(self.model, brres.models)
                if len(models) > 1:
                    multi_model = True
                    destination = destination[:-1 * len(self.ext)]
                else:
                    multi_model = False
                for mdl0 in models:
                    if multi_model:
                        converter.mdl_file = destination + '-' + mdl0.name + self.ext
                    converter.save_model(mdl0)

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
            for key in clip:
                item = clip[key]
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
        files_to_save = MATCHING.findAll(self.file, self.ACTIVE_FILES)
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
            x.run_cmd()

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
        elif type == 'brres':
            if self.type == 'tex0':
                convert_fmt = None
                try:
                    convert_fmt = self.value
                except AttributeError:
                    pass
                files = self.getFiles(type_id)
                for file in files:
                    tex = self.import_texture(file, convert_fmt)
                    if tex:
                        for x in self.SELECTED:
                            x.add_tex0(tex)
            elif self.type == 'mdl0':
                self.import_model(type_id)
        else:
            raise ParsingException(self.txt, 'command "Add" not supported for type {}'.format(type))

    def remove(self, type, type_id):
        """Remove command"""
        if self.SELECT_ID_NUMERIC and self.type_id is None:
            type_id = -1
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
        elif type == 'brres':
            if self.type == 'tex0':
                if self.SELECT_ID_NUMERIC:
                    for x in self.SELECTED:
                        x.remove_tex0_i(type_id)
                else:
                    for x in self.SELECTED:
                        x.remove_tex0(type_id)
            elif self.type == 'mdl0':
                if self.SELECT_ID_NUMERIC:
                    for x in self.SELECTED:
                        x.remove_mdl0_i(type_id)
                else:
                    for x in self.SELECTED:
                        x.remove_mdl0(type_id)
        else:
            raise ParsingException(self.txt, 'command "Remove" not supported for type {}'.format(type))

    def __str__(self):
        return "{} {}:{} for {} in file {} model {}".format(self.cmd,
                                                            self.key, self.value, self.name, self.file,
                                                            self.model)


def load_preset_file(dir):
    if dir is None:
        return False
    preset_path = os.path.join(dir, 'presets.txt')
    if os.path.exists(preset_path):
        Command.load_commandfile(preset_path)
        return True
    return False


def load_presets(app_dir):
    # Load presets in file directory
    loaded = True
    if not load_preset_file(app_dir):
        loaded = False
    # Load presets in cwd
    loaded_cwd = False
    cwd = os.getcwd()
    if app_dir != cwd:
        loaded_cwd = load_preset_file(cwd)
    if loaded or loaded_cwd:
        AUTO_FIXER.info('Presets loaded...', 5)
    else:
        AUTO_FIXER.info('No presets file detected', 3)
    return loaded
