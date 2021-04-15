import getopt
import os
import sys

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.matching import validBool, MATCHING, parse_color, validInt
from abmatt.brres.material_library import MaterialLibrary
from abmatt.brres.mdl0.material.layer import Layer
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.brres.mdl0.shader import Shader, Stage
from abmatt.brres.pat0.pat0 import Pat0
from abmatt.brres.srt0.srt0 import Srt0
from abmatt.brres.subfile import SubFile
from abmatt.brres.tex0 import Tex0
from abmatt.command import Command, NoSuchFile, Shell
from abmatt.config import Config
from abmatt.converters.material import Material
from abmatt.image_converter import ImgConverterI, ImgConverter


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
        Shader.REMOVE_UNUSED_LAYERS = Stage.REMOVE_UNUSED_LAYERS = Mdl0.REMOVE_UNUSED_REFS = validBool(val)
    except ValueError:
        pass


def load_config(app_dir, loudness=None, autofix_level=None):
    conf = Config.get_instance(os.path.join(app_dir, 'config.conf'))
    tmp_dir = os.path.join(app_dir, 'temp_files')
    MaterialLibrary.LIBRARY_PATH = os.path.join(app_dir, 'mat_lib.brres')
    converter = ImgConverter(tmp_dir)
    Tex0.converter = converter
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
    set_remove_unused(conf['remove_unused_refs'])
    try:
        Mdl0.DETECT_MODEL_NAME = validBool(conf['detect_model_name'])
    except ValueError:
        pass
    # try:
    #     Mdl0.DRAW_PASS_AUTO = validBool(conf['draw_pass_auto'])
    # except ValueError:
    #     pass
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
    return conf


VERSION = '0.9.42'
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
            AutoFix.get().exception(e, True)

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