#!/usr/bin/python
"""
ANoob's Brres Material Editor
For editing Mario Kart Wii files
"""

import getopt
import os
import sys
import Levenshtein
import fuzzywuzzy
from cmd import Cmd

from abmatt.brres import Brres
from abmatt.mdl0 import TexCoord
from abmatt.command import Command, ParsingException, NoSuchFile
from abmatt.autofix import AUTO_FIXER
from abmatt.config import Config
from matching import MATCHING

VERSION = '0.6.0'
USAGE = "USAGE: abmatt [-i -f <file> -b <brres-file> -c <command> -d <destination> -o -t <type> -k <key> -v <value> -n <name>]"


def hlp():
    """ displays help message """
    helpstr = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}
====================================================================================

| -a | --auto-fix | Automatic fix options are none, error, warning, check, all, and prompt. (0-5) The default is to fix at the check level without prompting.
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
    set xlu:true for xlu.* in course_model.brres
    set stage:0 colorscale:multiplyBy4 for bright_mat 
    info material for *
    copy material for * in original.brres
    paste material for * in course_model.brres
Example command line usage:
    abmatt -b course_model.brres -k xlu -v false -n mat1 -o
This opens course_model.brres in overwrite mode and disables xlu for material 'opaque_material'.
For more Help or if you want to contribute visit https://github.com/Robert-N7/abmatt
    '''
    print(helpstr.format(VERSION))
    print("{}".format(USAGE))


class Shell(Cmd):
    prompt = '>'

    @staticmethod
    def run(prefix, cmd):
        try:
            Command.run_commands([Command(prefix + ' ' + cmd)])
        except ParsingException as e:
            print('{}, Type "?" for help.'.format(e))
        except NoSuchFile as e:
            print(e)

    @staticmethod
    def complete_file(match_text):
        """Complete file if the last word is appropriate"""
        path = os.path.join(os.getcwd(), match_text)
        dir, start = os.path.split(path)
        files = os.listdir(dir)
        return [x for x in files if x.startswith(start)]

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
                files.append(name[name.rindex(text):])
        return files

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
                return self.complete_file(text)
            # last word is 'in' or a model or file
            possible = []
            if not 'model' in sel_words and text in 'model':
                possible.append('model')
            if 'file' not in sel_words:
                if last_word == 'in':
                    possible.extend(self.find_files(text))
                if text in 'file':
                    possible.append('file')
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
        print('paste <type> [for <selection>]')

    def complete_paste(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_copy(self, line):
        self.run('copy', line)

    def help_copy(self):
        print('copy <type> [for <selection>]')

    def complete_copy(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

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

    def complete_set(self, text, line, begid, endid):
        words = self.get_words(text, line)
        possible = []
        if not words:   # could bypass type
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
                keys = Command.TYPE_SETTING_MAP.get(words[0])
                if keys:
                    for key in keys:
                        if key.startswith(text):    # slightly weird way of saying, you gotta fill this in yourself
                            possible.append(key + ':*')
                            possible.append(key + ':?')
        return possible

    def do_add(self, line):
        self.run('add', line)

    def help_add(self):
        print('add <type> [for <selection>]')

    def complete_add(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_remove(self, line):
        self.run('remove', line)

    def help_remove(self):
        print('remove <type> [for <selection>]')

    def complete_remove(self, text, line, begid, endid):
        return self.generic_complete(text, self.get_words(text, line))

    def do_info(self, line):
        self.run('info', line)

    def help_info(self):
        print('info <type> [<key>] [for <selection>]')

    def complete_info(self, text, line, begid, endid):
        words = self.get_words(text, line)
        possible = []
        if not words:   # could be type key or 'for'
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
            prev = words[-1]
            if prev in Command.TYPE_SETTING_MAP:    # specified type?
                possible.extend([x for x in Command.TYPE_SETTING_MAP[prev] if x.startswith(text)])
            return possible

    def do_preset(self, line):
        self.run('preset', line)

    def help_preset(self):
        print('preset <preset> [for <selection>]')

    def complete_preset(self, text, line, begid, endid):
        words = self.get_words(text, line)
        if not words:
            return [x for x in Command.PRESETS if x.startswith(text)]
        elif len(words) == 1:
            return ['for'] if 'for'.startswith(text) else None
        else:
            return self.complete_selection(text, words[2:])     # need to check this

    def do_select(self, line):
        self.run('select', line)

    def help_select(self):
        print('select <name> [in <container>]')

    def complete_select(self, text, line, begid, endid):
        return self.complete_selection(text, self.get_words(text, line))

    def do_save(self, line):
        self.run('save', line)

    def help_save(self, line):
        print('save [<filename>] [as <destination>] [overwrite]')

    def complete_save(self, text, line, begid, endid):
        possible = []
        words = self.get_words(text, line)
        if not words:
            possible = [x for x in Command.OPEN_FILES if x.startswith(text)]
        elif words[-1] == 'as':
            possible = self.find_files(text)
        if 'overwrite'.startswith(text) and 'overwrite' not in words:
            possible.append('overwrite')
        if 'as'.startswith(text) and 'as' not in words:
            possible.append('as')

    def default(self, line):
        if line == 'x' or line == 'q':
            return self.do_quit(line)
        print('Syntax error, type ? for help')


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


def load_config(app_dir, loudness=None, autofix_level=None):
    conf = Config(os.path.join(app_dir, 'config.conf'))
    if not loudness:
        loudness = conf['loudness']
    if loudness:
        AUTO_FIXER.set_loudness(loudness)
    if not autofix_level:
        autofix_level = conf['autofix']
    if autofix_level:
        AUTO_FIXER.set_fix_level(autofix_level)
    max_brres_files = conf['max_brres_files']
    if max_brres_files:
        try:
            i = int(max_brres_files)
            Command.MAX_FILES_OPEN = i
        except:
            pass
    # Matching stuff
    MATCHING.set_case_sensitive(conf['case_sensitive'])
    MATCHING.set_partial_matching(conf['partial_matching'])
    MATCHING.set_regex_enable(conf['regex_matching'])


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
    interactive = overwrite = False
    type = "material"
    command = destination = brres_file = command_file = model = value = key = ""
    autofix = loudness = None
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
            autofix = arg
        elif opt in ("-l", "--loudness"):
            loudness = arg
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)

    # determine if application is a script file or frozen exe
    app_dir = None
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(os.path.dirname(sys.executable))
        app_dir = os.path.join(os.path.join(base_path, 'etc'), 'abmatt')
    elif __file__:
        app_dir = os.path.dirname(__file__)
    load_config(app_dir, loudness, autofix)
    load_presets(app_dir)
    cmds = []
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
            sys.exit(2)
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
        sys.exit(2)

    if command_file:
        filecmds = Command.load_commandfile(command_file)
        cmds = cmds + filecmds

    # Run Commands
    if cmds:
        if not Command.run_commands(cmds):
            sys.exit(1)
    if interactive:
        Shell().cmdloop('Interactive shell started...')

    # cleanup
    for file in Command.ACTIVE_FILES:
        file.close()


if __name__ == "__main__":
    main()
