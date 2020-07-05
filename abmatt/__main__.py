#!/usr/bin/python
"""
ANoob's Brres Material Editor
For editing Mario Kart Wii files
"""

import getopt
import os
import sys
from cmd import Cmd

import Levenshtein
import fuzzywuzzy
from abmatt.brres import Brres
from abmatt.mdl0 import TexCoord
from abmatt.command import Command, ParsingException, NoSuchFile
from abmatt.autofix import AUTO_FIXER

__version__ = "0.5.0"
USAGE = "USAGE: abmatt [-i -f <file> -b <brres-file> -d <destination> -o -t <type> -k <key> -v <value> -n <name>\
 -m <model>]"


def hlp():
    """ displays help message """
    helpstr = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}
====================================================================================

| Flag |Expanded| Description |
|---|---|---|
| -a | --auto-fix | Automatic fix options are none, error, warning, check, all, and prompt. (0-5) The default is to fix at the check level without prompting.
| -b | --brres | Brres file selection. |
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

File command format in extended BNF:
command =  cmd-prefix ['for' selection] EOL;
cmd-prefix = set | info | add | remove | select | preset | save | copy | paste;
set   = 'set' type setting;
info  = 'info' type [key | 'keys'];
add   = 'add' type;
remove = 'remove' type;
select = 'select' selection;    Note: does not support 'for' selection clause
preset = 'preset' preset_name;
save = 'save' [filename] ['as' destination] ['overwrite']
copy = 'copy' type;
paste = 'paste' type;

selection = name ['in' container]
container = ['brres' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id]
    | 'srt0' | 'srt0layer' [':' id] | 'pat0'
    | 'mdl0' | 'brres';

Example file commands:
    set xlu:true for xlu.* in course_model.brres      # Sets all materials starting with xlu to transparent
    set scale:(1,1) for *                 # Sets the scale for all layers to 1,1
    info layer:ef_arrowGradS        # Prints information about the layer 'ef_arrowGradS'
Example command line usage:
    abmatt -f course_model.brres -o -k xlu -v false -n opaque_material
This opens course_model.brres in overwrite mode and disables xlu for material 'opaque_material'.
For more Help or if you want to contribute visit https://github.com/Robert-N7/abmatt
    '''
    print(helpstr.format(__version__))
    print("{}".format(USAGE))


class Shell(Cmd):
    prompt = '>'

    def run(self, prefix, cmd):
        try:
            Command.run_commands([Command(prefix + ' ' + cmd)])
        except ParsingException as e:
            print('{}, Type "?" for help.'.format(e))
        except NoSuchFile as e:
            print(e)

    def do_paste(self, line):
        self.run('paste', line)

    def help_paste(self):
        print('paste <type> [for <selection>]')

    def do_copy(self, line):
        self.run('copy', line)

    def help_copy(self):
        print('copy <type> [for <selection>]')

    def do_quit(self, line):
        return True

    def help_quit(self):
        print('Ends the interactive shell.')

    do_EOF = do_quit
    help_EOF = help_quit

    def do_set(self, line):
        self.run('set', line)

    def help_set(self):
        print('set <type> <key>:<value> [for <selection>]')

    def do_add(self, line):
        self.run('add', line)

    def help_add(self):
        print('add <type>[:<id>] [for <selection>]')

    def do_remove(self, line):
        self.run('remove', line)

    def help_remove(self):
        print('remove <type>[:<id>] [for <selection>]')

    def do_info(self, line):
        self.run('info', line)

    def help_info(self):
        print('info <type> [<key>] [for <selection>]')

    def do_preset(self, line):
        self.run('preset', line)

    def help_preset(self):
        print('preset <preset> [for <selection>]')

    def do_select(self, line):
        self.run('select', line)

    def help_select(self):
        print('select <name> [in <container>]')

    def do_save(self, line):
        self.run('save', line)

    def help_save(self, line):
        print('save [<filename>] [as <destination>] [overwrite]')

    def default(self, line):
        if line == 'x' or line == 'q':
            return self.do_quit(line)
        print('Syntax error, type ? for help')


def load_preset_file(dir):
    preset_path = os.path.join(dir, 'presets.txt')
    if os.path.exists(preset_path):
        Command.load_commandfile(preset_path)
        return True
    return False


def load_presets():
    # Load presets in file directory
    loaded = True
    dir = os.path.dirname(os.path.abspath(__file__))
    if not load_preset_file(dir):
        dir = os.path.join(os.path.dirname(dir), 'etc')
        if not load_preset_file(dir):
            loaded = False
    # Load presets in cwd
    loaded_cwd = False
    cwd = os.getcwd()
    if dir != cwd:
        loaded_cwd = load_preset_file(cwd)
    loaded = loaded or loaded_cwd
    if loaded:
        AUTO_FIXER.info('Presets loaded...', 4)
    else:
        AUTO_FIXER.info('No presets file detected', 4)
    return loaded


def main():
    """ Main """
    global USAGE
    USAGE = USAGE.format(sys.argv[0])
    argv = sys.argv[1:]
    if not argv:
        print(USAGE)
        sys.exit(0)
    try:
        opts, args = getopt.getopt(argv, "a:hd:oc:t:k:v:n:b:m:f:iul:",
                                   ["help", "destination=", "overwrite",
                                    "command=", "type=", "key=", "value=",
                                    "name=", "brres=", "model=", "file=", "interactive",
                                    "auto-fix=", "loudness="])
    except getopt.GetoptError as e:
        print(e)
        print(USAGE)
        sys.exit(2)
    if args:
        print('Unknown option {}'.format(args))
        print(USAGE)
        sys.exit(2)
    interactive = overwrite = uv_divisor_zero = False
    type = "material"
    command = destination = brres_file = command_file = model = value = key = ""
    name = "*"
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            hlp()
            sys.exit()
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
            AUTO_FIXER.set_fix_level(arg)
        elif opt in ("-l", "--loudness"):
            AUTO_FIXER.set_loudness(arg)
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)

    load_presets()
    cmds = []
    if uv_divisor_zero:
        TexCoord.UV_DIVISOR_ZERO = True
    if destination:
        Command.DESTINATION = destination
        Brres.DESTINATION = destination
    if overwrite:
        Command.OVERWRITE = overwrite
        Brres.OVERWRITE = overwrite
    if brres_file:
        try:
            Command.updateFile(brres_file)
        except NoSuchFile as e:
            print(e)
            exit(2)
        if command:
            cmd = command + ' ' + type
            if key:
                cmd += ' ' + key
                if value:
                    cmd += ':' + value
            if name or model:
                cmd += ' for ' + name
                if model:
                    cmd += ' in model ' + model
            cmds.append(Command(cmd))
    elif command:
        print('File is required to run commands')
        print(USAGE)
        exit(2)

    if command_file:
        filecmds = Command.load_commandfile(command_file)
        cmds = cmds + filecmds

    # Run Commands
    if cmds:
        Command.run_commands(cmds)
    if interactive:
        Shell().cmdloop('Interactive shell started...')

    # cleanup
    for file in Command.ACTIVE_FILES:
        file.close()


if __name__ == "__main__":
    main()
