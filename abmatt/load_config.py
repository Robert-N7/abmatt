import getopt
import os
import sys
from cmd import Cmd

from brres import Brres
from autofix import AutoFix
from brres.lib.matching import validBool, MATCHING, parse_color, validInt
from brres.mdl0.layer import Layer
from brres.mdl0.mdl0 import Mdl0
from brres.mdl0.shader import Shader, Stage
from brres.pat0.pat0 import Pat0
from brres.srt0.srt0 import Srt0
from brres.subfile import SubFile
from brres.tex0 import Tex0, ImgConverterI
from command import Command, ParsingException, NoSuchFile
from config import Config
from converters.material import Material


def set_rename_unknown(val):
    try:
        Mdl0.RENAME_UNKNOWN_REFS = Layer.RENAME_UNKNOWN_REFS = Pat0.RENAME_UNKNOWN_REFS = validBool(val)
    except ValueError:
        pass


def set_remove_unknown(val):
    try:
        Mdl0.REMOVE_UNKNOWN_REFS = Layer.REMOVE_UNKNOWN_REFS = Pat0.REMOVE_UNKNOWN_REFS = Srt0.REMOVE_UNKNOWN_REFS = \
            validBool(val)
    except ValueError:
        pass


def set_remove_unused(val):
    try:
        Shader.REMOVE_UNUSED_LAYERS = Stage.REMOVE_UNUSED_LAYERS = validBool(val)
    except ValueError:
        pass


def load_config(app_dir, loudness=None, autofix_level=None):
    conf = Config.get_instance(os.path.join(app_dir, 'config.conf'))
    if not loudness:
        loudness = conf['loudness']
    if loudness:
        try:
            AutoFix.get().set_loudness(loudness)
        except ValueError:
            AutoFix.get().warn('Invalid loudness level {}'.format(loudness))
    if not len(conf):
        AutoFix.get().warn('No configuration detected (etc/abmatt/config.conf).')
        return
    Command.set_max_brres_files(conf)
    # Matching stuff
    MATCHING.set_case_sensitive(conf['case_sensitive'])
    MATCHING.set_partial_matching(conf['partial_matching'])
    MATCHING.set_regex_enable(conf['regex_matching'])
    # Autofixes
    try:
        SubFile.FORCE_VERSION = validBool(conf['force_version'])
    except ValueError:
        pass
    try:
        Brres.REMOVE_UNUSED_TEXTURES = validBool(conf['remove_unused_textures'])
    except ValueError:
        pass
    try:
        Layer.MINFILTER_AUTO = validBool(conf['minfilter_auto'])
    except ValueError:
        pass
    set_rename_unknown(conf['rename_unknown_refs'])
    set_remove_unknown(conf['remove_unknown_refs'])
    set_remove_unused(conf['remove_unused_layers'])
    try:
        Mdl0.DETECT_MODEL_NAME = validBool(conf['detect_model_name'])
    except ValueError:
        pass
    try:
        Mdl0.DRAW_PASS_AUTO = validBool(conf['draw_pass_auto'])
    except ValueError:
        pass
    try:
        Shader.MAP_ID_AUTO = validBool(conf['map_id_auto'])
    except ValueError:
        pass
    try:
        Material.DEFAULT_COLOR = parse_color(conf['default_material_color'])
    except ValueError:
        pass
    try:
        Tex0.RESIZE_TO_POW_TWO = validBool(conf['resize_pow_two'])
    except ValueError:
        pass
    try:
        Tex0.set_max_image_size(validInt(conf['max_image_size'], 0, 10000))
    except (TypeError, ValueError):
        pass
    resample = conf['img_resample']
    if resample is not None:
        ImgConverterI.set_resample(resample)
    Brres.MATERIAL_LIBRARY = conf['material_library']
    Brres.TEMP_DIR = conf['temp_dir']
    return conf


VERSION = '0.8.0'
USAGE = "USAGE: abmatt [command_line][--interactive -f <file> -b <brres-file> -d <destination> --overwrite]"


def hlp(cmd=None):
    """ displays help message """
    if cmd:
        cmd_help = {'set': Shell.help_set, 'info': Shell.help_info, 'add': Shell.help_add, 'remove': Shell.help_remove,
                    'select': Shell.help_select, 'preset': Shell.help_preset, 'save': Shell.help_save,
                    'copy': Shell.help_copy, 'paste': Shell.help_paste, 'convert': Shell.help_convert}
        help_fptr = cmd_help.get(cmd)
        if help_fptr:
            help_fptr(None)
            return
        print('Unknown command {}'.format(cmd))
    helpstr = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}
commands = set | info | add | remove | select | preset | save | copy | paste | convert
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id]
    | 'srt0' | 'srt0layer' [':' id] | 'pat0'
    | 'mdl0' | 'brres';
To see what keys are available, try `info keys`
====================================================================================
## Command Line Usage:
| -b | --brres | Brres file selection. |
| -c | --command | Command name to run. |
| -d | --destination | The file path to be written to. Mutliple destinations are not supported. |
| -f | --file | File with ABMatt commands to be processed as specified in file format. |
| -h | --help | Displays a help message about program usage. |
| -i | --interactive | Interactive shell mode. |
| -k | --key | Setting key to be updated. |
| -l | --loudness | Sets the verbosity level. (0-5)
| -m | --model | Model selection. |
| -n | --name | Material or layer name or regular expression to be found. |
| -o | --overwrite | Overwrite existing files.  |
| -t | --type | Type selection. |
| -v | --value | Value to set corresponding with key. (set command) |

command_line =  cmd-prefix ['for' selection] EOL;
cmd-prefix = set | info | add | remove | select | preset | save | copy | paste | convert;
set   = 'set' type setting;
info  = 'info' type [key | 'keys'];
add   = 'add' type;
remove = 'remove' type;
select = 'select' selection;
preset = 'preset' preset_name;
save = 'save' [filename] ['as' destination] ['overwrite']
copy = 'copy' type;
paste = 'paste' type;
convert = 'convert' filename ['to' destination] ['no-colors'] ['no-normals']

selection = name ['in' container]
container = ['brres' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id]
    | 'srt0' | 'srt0layer' [':' id] | 'pat0'
    | 'mdl0' [':' id] | 'tex0' [':' id] | 'brres';

For more Help or if you want to contribute visit https://github.com/Robert-N7/abmatt
    '''
    print(helpstr.format(VERSION))
    print("{}".format(USAGE))


class Shell(Cmd, object):
    prompt = '>'

    def __init__(self):
        super(Shell, self).__init__()
        self.cmd_queue = []

    def run(self, prefix, cmd):
        line = prefix + ' ' + cmd
        self.cmd_queue.append(line)
        try:
            Command.run_commands([Command(line)])
        except (ParsingException, NoSuchFile) as e:
            AutoFix.get().error(e)

    @staticmethod
    def complete_material_name(match_text):
        matches = []
        for x in Command.MODELS:
            matches.extend([mat for mat in x.materials if mat.name.startswith(match_text)])
        return matches

    @staticmethod
    def complete_model_name(match_text):
        matches = []
        for x in Command.ACTIVE_FILES:
            matches.extend([mdl for mdl in x.models if mdl.name.startswith(match_text)])
        return matches

    @staticmethod
    def complete_type(match_text):
        return [x for x in Command.TYPE_SETTING_MAP if x.startswith(match_text)]

    @staticmethod
    def complete_key(match_text, type=None):
        if type:
            matches = [x for x in Command.TYPE_SETTING_MAP[type] if x.startswith(match_text)]
        else:
            matches = []
            for key, vals in enumerate(Command.TYPE_SETTING_MAP):
                matches.extend([val for val in vals if val.startswith(match_text)])
        return matches

    @staticmethod
    def find_files(path, text):
        """finds the files at path, that start with text (removes anything on the path before text)"""
        directory, name = os.path.split(path)
        if not directory:
            directory = "."
        files = []
        for file in os.listdir(directory):
            if file.startswith(name):
                files.append(file[name.rindex(text):])
        return files

    @staticmethod
    def construct_file_path(sel_words, start_file=False):
        path = None
        for x in sel_words:
            if x in ('in', 'to'):
                start_file = True
            elif x == 'model':
                start_file = False
            elif x == 'file':
                start_file = True
            elif start_file:
                path = x if path is None else os.path.join(path, x)
        return path

    def complete_selection(self, text, sel_words):
        if not sel_words:
            return self.complete_material_name(text)
        elif 'in' not in sel_words:
            return ['in'] if not text or text in 'in' else None
        else:
            last_word = sel_words[-1]
            if last_word == 'model':
                return self.complete_model_name(text)
            elif last_word == 'file':
                return self.find_files(text, text)
            # last word is 'in' or a model or file
            possible = []
            if 'model'.startswith(text):
                possible.append('model')
            elif 'file'.startswith(text):
                possible.append('file')
            sel_words.append(text)
            possible.extend(self.find_files(self.construct_file_path(sel_words), text))
            return possible

    def generic_complete(self, text, words, for_sel_index=1):
        """ :param text: text to complete
            :param words: list of words in the line minus the command
            :param for_sel_index: the index where the word 'for' should be in words
        """
        if not words:
            return self.complete_type(text)
        if len(words) == for_sel_index:
            return ['for'] if 'for'.startswith(text) else None
        elif len(words) > for_sel_index:
            return self.complete_selection(text, words[for_sel_index + 1:])

    def get_words(self, text, line):
        if text:  # remove text from end
            line = line[:-1 - len(text)]
        return line.split(' ')[1:]  # remove the first command

    def do_paste(self, line):
        self.run('paste', line)

    def help_paste(self):
        print('USAGE: paste <type> [for <selection>]')

    def complete_paste(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_copy(self, line):
        self.run('copy', line)

    def help_copy(self):
        print('USAGE: copy <type> [for <selection>]')

    def complete_copy(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_quit(self, line):
        return True

    def help_quit(self):
        print('Ends the interactive shell.')

    do_EOF = do_quit

    def do_set(self, line):
        self.run('set', line)

    def help_set(self):
        print('USAGE: set <type> <key>:<value> [for <selection>]')

    def complete_set(self, text, line, begid, endid):
        words = self.get_words(text, line)
        possible = []
        if not words:  # could bypass type
            for key in Command.TYPE_SETTING_MAP:
                if key.startswith(text):
                    possible.append(key)
                for setting in Command.TYPE_SETTING_MAP[key]:
                    if setting.startswith(text):
                        possible.append(setting + ':?')
                        possible.append(setting + ':*')
        else:
            # Check for 'for'
            try:
                for_index = words.index('for')
                return self.complete_selection(text, words[for_index + 1:])
            except ValueError:
                if 'for'.startswith(text):
                    possible.append('for')
            if len(words) < 2:  # maybe a key:val pair, more than that it can't be
                keys = Command.TYPE_SETTING_MAP.get(words[0].split(':')[0])
                if keys:
                    for key in keys:
                        if key.startswith(text):  # slightly weird way of saying, you gotta fill this in yourself
                            possible.append(key + ':*')
                            possible.append(key + ':?')
        return possible

    def do_add(self, line):
        self.run('add', line)

    def help_add(self):
        print('USAGE: add <type> [for <selection>]')

    def complete_add(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_remove(self, line):
        self.run('remove', line)

    def help_remove(self):
        print('USAGE: remove <type> [for <selection>]')

    def complete_remove(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_info(self, line):
        self.run('info', line)

    def help_info(self):
        print('USAGE: info <type> [<key>] [for <selection>]')

    def complete_info(self, text, line, begid, endid):
        words = self.get_words(text, line)
        possible = []
        if not words:  # could be type key or 'for'
            for x in Command.TYPE_SETTING_MAP:
                if x.startswith(text):
                    possible.append(x)
                for key in Command.TYPE_SETTING_MAP[x]:
                    if key.startswith(text):
                        possible.append(key)
            if 'for'.startswith(text):
                possible.append('for')
            return possible
        else:
            # check if for is present (selection)
            try:
                for_index = words.index('for')
                return self.complete_selection(text, words[for_index + 1:])
            except ValueError:
                if 'for'.startswith(text):
                    possible.append('for')
            sel_type = words[0].split(':')[0]
            settings = Command.TYPE_SETTING_MAP.get(sel_type)
            if settings:  # specified type?
                possible.extend([x for x in settings if x.startswith(text)])
            return possible

    def do_preset(self, line):
        self.run('preset', line)

    def help_preset(self):
        print('USAGE: preset <preset> [for <selection>]')

    def complete_preset(self, text, line, begid, endid):
        words = self.get_words(text, line)
        if not words:
            return [x for x in Command.PRESETS if x.startswith(text)]
        elif len(words) == 1:
            return ['for'] if 'for'.startswith(text) else None
        else:
            return self.complete_selection(text, words[2:])  # need to check this

    def do_select(self, line):
        self.run('select', line)

    def help_select(self):
        print('USAGE: select <name> [in <container>]')

    def complete_select(self, text, line, begid, endid):
        return self.complete_selection(text, self.get_words(text, line))

    def do_save(self, line):
        self.run('save', line)

    def help_save(self):
        print('USAGE: save [<filename>] [as <destination>] [overwrite]')

    def complete_save(self, text, line, begid, endid):
        possible = []
        words = self.get_words(text, line)
        if not words:
            possible = [x for x in Command.OPEN_FILES if x.startswith(text)]
        elif 'as' in words:
            file_words = words[words.index('as') + 1:]
            if file_words:
                path = file_words.pop(0)
                for x in file_words:
                    path = os.path.join(path, x)
                path = os.path.join(path, text)
            else:
                path = text
            try:
                possible = self.find_files(path, text)
            except OSError as e:
                pass
        if 'overwrite'.startswith(text) and 'overwrite' not in words:
            possible.append('overwrite')
        if 'as'.startswith(text) and 'as' not in words:
            possible.append('as')
        return possible

    def do_dump(self, line):
        words = line.split()
        if not words:
            print('USAGE: dump <filename> [overwrite]')
        elif not self.cmd_queue:
            print('Nothing in queue.')
        else:
            file = words.pop(0)
            overwrite = True if 'overwrite' in words or Command.OVERWRITE else False
            if os.path.exists(file) and not overwrite:
                AutoFix.get().error('File {} already exists!'.format(file))
            else:
                with open(file, 'w') as f:
                    f.write('\n'.join(self.cmd_queue))

    def help_dump(self):
        print('Dumps interactive shell commands to file.')
        print('USAGE: dump <filename> [overwrite]')

    def do_clear(self, line):
        self.cmd_queue = []

    def help_clear(self):
        print('Clears the interactive shell command queue.')

    def do_convert(self, line):
        self.run('convert', line)

    def complete_convert(self, text, line, begid, endid):
        words = self.get_words(text, line)
        possible = self.find_files(self.construct_file_path(words), text)
        return possible

    def help_convert(self):
        print('Converts dae or obj model to/from brres.\nUsage: convert <filename> [to <destination>]')

    def default(self, line):
        if line == 'x' or line == 'q':
            return self.do_quit(line)
        print('Syntax error, type ? for help')


def parse_args(argv, app_dir):
    interactive = overwrite = debug = False
    cmd_string = type = ""
    command = destination = brres_file = command_file = model = value = key = ""
    autofix = loudness = None
    name = None
    do_help = False
    for i in range(len(argv)):
        if argv[i][0] == '-':
            if i != 0:
                cmd_string = ' '.join(argv[:i])
                argv = argv[i:]
            break

    try:
        opts, args = getopt.getopt(argv, "hd:oc:t:k:v:n:b:m:f:iul:g",
                                   ["help", "destination=", "overwrite",
                                    "command=", "type=", "key=", "value=",
                                    "name=", "brres=", "model=", "file=", "interactive",
                                    "loudness=", "debug"])
    except getopt.GetoptError as e:
        print(e)
        print(USAGE)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            do_help = True
        elif opt in ('-b', '--brres'):
            brres_file = arg
        elif opt in ("-f", "--file"):
            command_file = arg
        elif opt in ("-d", "--destination"):
            destination = arg
        elif opt in ("-o", "--overwrite"):
            overwrite = True
        elif opt in ("-k", "--key"):
            key = arg
        elif opt in ("-v", "--value"):
            value = arg
        elif opt in ("-t", "--type"):
            type = arg
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-m", "--model"):
            model = arg
        elif opt in ("-c", "--command"):
            command = arg
        elif opt in ("-i", "--interactive"):
            interactive = True
        elif opt in ("-a", "--auto-fix"):
            autofix = arg
        elif opt in ("-l", "--loudness"):
            loudness = arg
        elif opt in ("-g", "--debug"):
            debug = True
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)
    if args:
        if cmd_string:
            cmd_string += ' ' + ' '.join(args)
        else:
            cmd_string = ' '.join(args)
    if do_help:
        if not command and cmd_string:
            command = cmd_string.split()[0]
        hlp(command)
        sys.exit()

    app_dir = os.path.join(os.path.join(os.path.dirname(os.path.dirname(app_dir)), 'etc'), 'abmatt')
    if debug and loudness is None:
        loudness = 5
    config = load_config(app_dir, loudness, autofix)
    Command.APP_DIR = app_dir
    Command.DEBUG = debug
    cmds = []
    if cmd_string:
        cmds.append(Command(cmd_string))
    if command:
        cmd = command + ' ' + type
        if key:
            cmd += ' ' + key
            if value:
                cmd += ':' + value
        if not name and key != 'keys':
            name = '*'
        if name or model:
            cmd += ' for ' + name
            if model:
                cmd += ' in model ' + model
        cmds.append(Command(cmd))
    if destination:
        Command.DESTINATION = destination
        Brres.DESTINATION = destination
    if overwrite:
        Command.OVERWRITE = overwrite
        Brres.OVERWRITE = overwrite
    if brres_file:
        try:
            Command.updateSelection(brres_file)
        except NoSuchFile as e:
            AutoFix.get().error(e)
            sys.exit(2)

    if command_file:
        try:
            filecmds = Command.load_commandfile(command_file)
            if filecmds:
                cmds = cmds + filecmds
        except NoSuchFile as err:
            AutoFix.get().error(err)

    # Run Commands
    if cmds:
        if not Command.run_commands(cmds):
            sys.exit(1)
    if interactive:
        Shell().cmdloop('Interactive shell started...')
    return Command.OPEN_FILES