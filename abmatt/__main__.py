#!/usr/bin/python
"""
ANoob's Brres Material Editor
For editing Mario Kart Wii files
"""

import getopt
import os
import sys
from cmd import Cmd

from abmatt.brres import Brres
from abmatt.command import Command, ParsingException, NoSuchFile
from brres.lib.autofix import AUTO_FIXER
from abmatt.config import load_config

VERSION = '0.6.1'
USAGE = "USAGE: abmatt [-i -f <file> -b <brres-file> -c <command> -d <destination> -o -t <type> -k <key> -v <value> -n <name>]"


def hlp(cmd=None):
    cmd_help = {'set': Shell.help_set, 'info': Shell.help_info, 'add': Shell.help_add, 'remove': Shell.help_remove,
                'select': Shell.help_select, 'preset': Shell.help_preset, 'save': Shell.help_save,
                'copy': Shell.help_copy, 'paste': Shell.help_paste}
    help_fptr = cmd_help.get(cmd)
    if help_fptr:
        help_fptr(None)
        return
    """ displays help message """
    helpstr = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}
commands = set | info | add | remove | select | preset | save | copy | paste
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
        except ParsingException as e:
            print('{}, Type "?" for help.'.format(e))
        except NoSuchFile as e:
            AUTO_FIXER.error(e)

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
    def construct_file_path(sel_words):
        start_file = False
        path = None
        for x in sel_words:
            if x == 'in':
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
                AUTO_FIXER.error('File {} already exists!'.format(file))
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
    type = ""
    command = destination = brres_file = command_file = model = value = key = ""
    autofix = loudness = None
    name = None
    do_help = False
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
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)

    if do_help:
        hlp(command)
        sys.exit()

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
            Command.updateFile(brres_file)
        except NoSuchFile as e:
            AUTO_FIXER.error(e)
            sys.exit(2)
    elif command and (command != 'info' or key != 'keys' and type != 'keys'):
        print('File is required to run commands')
        print(USAGE)
        sys.exit(2)

    if command_file:
        try:
            filecmds = Command.load_commandfile(command_file)
            if filecmds:
                cmds = cmds + filecmds
        except NoSuchFile as err:
            AUTO_FIXER.error(err)

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
