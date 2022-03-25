import getopt
import os
import sys

from abmatt.autofix import AutoFix
from abmatt.brres import Brres
from abmatt.brres.lib.matching import validBool, MATCHING, parse_color, validInt
from abmatt.brres.material_library import MaterialLibrary
from abmatt.brres.mdl0.material.layer import Layer
from abmatt.brres.mdl0.material.material import Material
from abmatt.brres.mdl0.mdl0 import Mdl0
from abmatt.brres.mdl0.shader import Shader, Stage
from abmatt.brres.pat0.pat0 import Pat0
from abmatt.brres.srt0.srt0 import Srt0
from abmatt.brres.subfile import SubFile
from abmatt.brres.tex0 import Tex0
from abmatt.command import Command, NoSuchFile, Shell
from abmatt.config import Config
from abmatt.converters.convert_lib import Converter
from abmatt.converters.geometry import Geometry
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


def load_config(app_dir=None, loudness=None, autofix_level=None):
    if app_dir is None:
        app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'etc', 'abmatt')
    conf = Config.get_instance(os.path.join(app_dir, 'config.conf'))
    tmp_dir = os.path.join(app_dir, 'temp_files')
    converter = ImgConverter(tmp_dir)
    Tex0.converter = converter
    if not loudness:
        loudness = conf['loudness']
    if loudness:
        try:
            AutoFix.set_loudness(loudness)
        except ValueError:
            AutoFix.warn('Invalid loudness level {}'.format(loudness))
    AutoFix.set_fix_level(autofix_level, turn_off_fixes)
    if not len(conf):
        AutoFix.warn('No configuration detected (etc/abmatt/config.conf).')
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
    try:
        Geometry.ENABLE_VERTEX_COLORS = validBool(conf['enable_vertex_colors'])
    except ValueError:
        pass
    Converter.ENCODE_PRESET = conf['encode_preset']
    resample = conf['img_resample']
    if resample is not None:
        ImgConverterI.set_resample(resample)
    if conf['material_library']:
        MaterialLibrary.LIBRARY_PATH = conf.config.get('material_library')
    else:
        MaterialLibrary.LIBRARY_PATH = os.path.join(app_dir, 'mat_lib.brres')
    return conf


VERSION = '1.3.1'
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
====================================================================================
Command Line Usage:
abmatt [command_line][flags]

| -a | --auto-fix | Set the autofix level (0 to turn off fixes). |
| -b | --brres | Brres file selection. |
| -c | --command | Command name to run. |
| -d | --destination | The file path to be written to. Mutliple destinations are not supported. |
| -f | --file | File with ABMatt commands to be processed as specified in file format. |
| -h | --help | Displays a help message about program usage. |
| -i | --interactive | Interactive shell mode. |
| -l | --loudness | Sets the verbosity level. (0-5)
| -o | --overwrite | Overwrite existing files.  |
|   | --moonview | Treat the Brres as Moonview course, adjusting material names. |

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
convert = 'convert' filename ['to' destination] ['include' poly-list] ['exclude' poly-list] [convert-flags]
load = 'load' command-file

convert-flags = ['patch'] ['no-colors'] ['no-normals'] ['single-bone'] ['no-uvs']
poly-list = [polygon-name[,polygon-name]*]

selection = name ['in' container]
container = ['brres' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id]
    | 'srt0' | 'srt0layer' [':' id] | 'pat0'
    | 'mdl0' [':' id] | 'tex0' [':' id] | 'brres';

For more Help or if you want to contribute visit https://github.com/Robert-N7/abmatt
    '''
    print(helpstr.format(VERSION))
    print("{}".format(USAGE))


def turn_off_fixes():
    SubFile.FORCE_VERSION = False
    Brres.REMOVE_UNUSED_TEXTURES = False
    Layer.MINFILTER_AUTO = False
    Mdl0.DETECT_MODEL_NAME = False
    Shader.MAP_ID_AUTO = False
    Tex0.RESIZE_TO_POW_TWO = False
    Geometry.ENABLE_VERTEX_COLORS = False
    Mdl0.RENAME_UNKNOWN_REFS = False
    Mdl0.REMOVE_UNKNOWN_REFS = False
    Shader.REMOVE_UNUSED_LAYERS = False


def parse_args(argv, app_dir):
    interactive = overwrite = debug = False
    type = ""
    cmd_args = None
    command = destination = brres_file = command_file = model = value = key = ""
    autofix = loudness = None
    name = None
    no_normals = no_colors = single_bone = no_uvs = moonview = patch = False
    do_help = False
    for i in range(len(argv)):
        if argv[i][0] == '-':
            if i != 0:
                cmd_args = argv[:i]
                argv = argv[i:]
            break

    try:
        opts, args = getopt.gnu_getopt(argv, "ahd:oc:t:k:v:n:b:m:f:iul:g",
                                   ["auto-fix", "help", "destination=", "overwrite",
                                    "command=", "type=", "key=", "value=",
                                    "name=", "brres=", "model=", "file=", "interactive",
                                    "loudness=", "debug",
                                    "single-bone", "no-colors", "no-normals", "no-uvs", "moonview",
                                    "patch"])
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
        elif opt == '--single-bone':
            single_bone = True
        elif opt == '--no-normals':
            no_normals = True
        elif opt == '--no-colors':
            no_colors = True
        elif opt == '--no-uvs':
            no_uvs = True
        elif opt == '--patch':
            patch = True
        elif opt == '--moonview':
            moonview = True
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)
    if args:
        if cmd_args:
            cmd_args.extend(args)
        else:
            cmd_args = args
    if do_help:
        if not command and cmd_args:
            command = cmd_args[0]
        hlp(command)
        sys.exit()

    app_dir = os.path.dirname(os.path.dirname(app_dir))
    test_app_dir = app_dir
    while not os.path.exists(os.path.join(test_app_dir, 'etc')):
        test_app_dir = os.path.dirname(test_app_dir)
        if not test_app_dir or test_app_dir.endswith(':\\'):
            test_app_dir = app_dir
            break
    app_dir = test_app_dir
    etc_path = os.path.join(test_app_dir, 'etc')
    if not os.path.exists(etc_path):
        AutoFix.warn('Failed to find folder "etc". Creating it...')
        os.mkdir(etc_path)
    etc_path = os.path.join(etc_path, 'abmatt')
    if not os.path.exists(etc_path):
        os.mkdir(etc_path)
        with open(os.path.join(etc_path, 'config.conf'), 'w') as f:
            f.write('''
# ----------------------------------------------------------------------------------------------
# ABMatt Configuration file
# IMPORTANT: re-installing abmatt may overwrite your configurations. Remember to back them up!
# ----------------------------------------------------------------------------------------------

# General
loudness=3              # verbosity between 0-5
max_brres_files=10      # maximum files open (command line only)

# Encoding
encode_preset=          # preset to run upon loading a model
encode_preset_only_on_new=True      # only run the preset if not replacing model and no previous json settings detected
enable_vertex_colors=True   # enables vertex colors if colors are loaded in geometry

# Materials
material_library=         # brres file path, materials with matching names are replaced when creating model
default_material_color=200,200,200,255      # RGBA color used for materials with no map layers

# Textures
remove_unused_textures=True     # removes textures that aren't used
resize_pow_two=True             # automatically resize to a power of 2
max_image_size=1024             # maximum size
minfilter_auto=True             # sets the minfilter to linear when there's no mipmaps, linear_mipmap_linear if there is
img_resample=bicubic            # Used when resizing images, (nearest|box|bilinear|hamming|bicubic|lanczos)

# Auto fixes
detect_model_name=True      # detects what model name it should be according to file name (vrcorn, course, map)
remove_unused_refs=False    # removes refs that aren't used
rename_unknown_refs=True    # try to rename unknown refs
remove_unknown_refs=True    # if rename_unknown_refs enabled, renaming is tried first and then removal
force_version=True          # forces version to the expected mkwii version
map_id_auto=True            # switches/removes shader stage map id when not found
invalid_divisor_zero=True   # zeros out invalid divisors

# Matching functions
regex_matching=on_none_found    # True|False|on_none_found
partial_matching=on_none_found  # True|False|on_none_found
case_sensitive=False            # True|False
''')

    if debug and loudness is None:
        loudness = 5
    config = load_config(etc_path, loudness, autofix)
    Command.APP_DIR = etc_path
    Command.DEBUG = debug
    Brres.MOONVIEW = moonview
    cmds = []
    if cmd_args:
        if cmd_args[0] == 'convert':
            if single_bone:
                cmd_args.append('--single-bone')
            if no_colors:
                cmd_args.append('--no-colors')
            if no_normals:
                cmd_args.append('--no-normals')
            if no_uvs:
                cmd_args.append('--no-uvs')
            if patch:
                cmd_args.append('--patch')
        cmds.append(Command(arg_list=cmd_args))
    if command:
        args = [command, type]
        if key:
            if value:
                args.append(key + ':' + value)
            else:
                args.append(key)
        if not name and key != 'keys':
            name = '*'
        if name or model:
            args.extend(['for', name])
            if model:
                args.extend(['in', 'model', model])
        if command == 'convert':
            if single_bone:
                args.append('--single-bone')
            if no_colors:
                args.append('--no-colors')
            if no_normals:
                args.append('--no-normals')
            if no_uvs:
                args.append('--no-uvs')
            if patch:
                args.append('--patch')
        cmds.append(Command(arg_list=args))
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
            AutoFix.exception(e, True)

    if command_file:
        try:
            filecmds = Command.load_commandfile(command_file)
            if filecmds:
                cmds = cmds + filecmds
        except NoSuchFile as err:
            AutoFix.error(err)

    # Run Commands
    if cmds:
        if not Command.run_commands(cmds):
            sys.exit(1)
    if interactive:
        Shell().cmdloop('Interactive shell started...')
    return Brres.OPEN_FILES