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
from abmatt.command import Command, run_commands, ParsingException, load_commandfile

__version__ = "0.2.0"
USAGE = "Usage: {} -f <file> [-d <destination> -o -c <commandfile> -k <key> -v <value>\
 -n <name> -m <model> -i -s] "


def hlp():
    """ displays help message """
    helpstr = '''
====================================================================================
ANOOB'S BRRES MATERIAL TOOL
Version {}

      >>       >==>    >=>     >===>          >===>      >=>>=>    >=>   >=>>=>
     >>=>      >> >=>  >=>   >=>    >=>     >=>    >=>   >>   >=>   >> >=>    >=>
    >> >=>     >=> >=> >=> >=>        >=> >=>        >=> >>    >=>      >=>
   >=>  >=>    >=>  >=>>=> >=>        >=> >=>        >=> >==>>=>          >=>
  >=====>>=>   >=>   > >=> >=>        >=> >=>        >=> >>    >=>           >=>
 >=>      >=>  >=>    >>=>   >=>     >=>    >=>     >=>  >>     >>     >=>    >=>
>=>        >=> >=>     >=>     >===>          >===>      >===>>=>        >=>>=>

>=>>=>    >======>     >======>     >=======>   >=>>=>
>>   >=>  >=>    >=>   >=>    >=>   >=>       >=>    >=>
>>    >=> >=>    >=>   >=>    >=>   >=>        >=>
>==>>=>   >> >==>      >> >==>      >=====>      >=>
>>    >=> >=>  >=>     >=>  >=>     >=>             >=>
>>     >> >=>    >=>   >=>    >=>   >=>       >=>    >=>
>===>>=>  >=>      >=> >=>      >=> >=======>   >=>>=>

>=>       >=>       >>       >===>>=====> >=======> >======>     >=>       >>       >=>
>> >=>   >>=>      >>=>           >=>     >=>       >=>    >=>   >=>      >>=>      >=>
>=> >=> > >=>     >> >=>          >=>     >=>       >=>    >=>   >=>     >> >=>     >=>
>=>  >=>  >=>    >=>  >=>         >=>     >=====>   >> >==>      >=>    >=>  >=>    >=>
>=>   >>  >=>   >=====>>=>        >=>     >=>       >=>  >=>     >=>   >=====>>=>   >=>
>=>       >=>  >=>      >=>       >=>     >=>       >=>    >=>   >=>  >=>      >=>  >=>
>=>       >=> >=>        >=>      >=>     >=======> >=>      >=> >=> >=>        >=> >=======>

>===>>=====>     >===>          >===>      >=>
     >=>       >=>    >=>     >=>    >=>   >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>     >=>        >=> >=>        >=> >=>
     >=>       >=>     >=>    >=>     >=>  >=>
     >=>         >===>          >===>      >=======>
====================================================================================

| Flag |Expanded| Description |
|---|---|---|
| -c | --commandfile | File with ABMatT commands to be processed as specified in file format. |
| -d | --destination | The file name to be written to. Mutliple destinations are not supported. |
| -f | --file | The brres file name to be read from |
| -h | --help | Displays a help message about program usage. |
| -i | --info | Information flag that generates additional informational output. |
| -k | --key | Setting key to be updated. See [File Format](## File Format) for keys. |
| -m | --model | The name of the model to search in. |
| -n | --name | Material or layer name or regular expression to be found. |
| -o | --overwrite | Overwrite existing files. The default is to not overwrite the input file or any other file unless this flag is used. |
| -s | --shell | Interactive shell mode. |
| -t | --type | Type (material, layer, shader, stage) |
| -v | --value | Setting value to be paired with a key. |

File command format in extended BNF:
command = (set | info | add | remove | select | preset) ['for' selection] EOL;
set   = 'set' type setting;
info  = 'info' type [key];
add   = 'add' type;
remove = 'remove' type;
select = 'select' selection;    Note: does not support 'for' selection clause
preset = 'preset' preset_name;

selection = name ['in' container]
container = ['file' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id];
setting =  key ':' value; NOTE: No spaces allowed in key:value pairs

Example file commands:
    set xlu:true for xlu.* in model course      # Sets all materials in course starting with xlu to transparent
    set scale:(1,1) for *                 # Sets the scale for all layers to 1,1
    info layer:ef_arrowGradS        # Prints information about the layer 'ef_arrowGradS'
Example command line usage:
    abmatt -f course_model.brres -o -k xlu -v false -n opaque_material
This opens course_model.brres in overwrite mode and disables xlu for material 'opaque_material'.
For more Help or if you want to contribute visit https://github.com/Robert-N7/ABMatT
    '''
    print(helpstr.format(__version__))
    print("Usage: {}".format(USAGE))


class Shell(Cmd):
    prompt = '>'

    def run(self, prefix, cmd):
        try:
            run_commands([Command(prefix + ' ' + cmd)])
        except ParsingException as e:
            print('{}, Type "?" for help.'.format(e))

    def do_quit(self, line):
        print('Stopping shell...')
        return True

    def help_quit(self):
        print('Ends the interractive shell.')

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

    def default(self, line):
        if line == 'x' or line == 'q':
            return self.do_quit(line)
        print('Syntax error, type ? for help')


def main():
    """ Main """
    global USAGE
    USAGE = USAGE.format(sys.argv[0])
    argv = sys.argv[1:]
    if not argv:
        hlp()
        sys.exit(0)
    try:
        opts, args = getopt.getopt(argv, "hf:d:ok:v:n:m:c:t:is",
                                   ["help", "file=", "destination=", "overwrite",
                                    "type=", "key=", "value=",
                                    "name=", "model=", "info", "commandfile=", "shell"])
    except getopt.GetoptError:
        print(USAGE)
        sys.exit(2)
    filename = ""
    destination = ""
    shell_mode = info = overwrite = False
    type = "material"
    setting = ""
    value = ""
    name = ".*"
    model = ""
    commandfile = ""
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            hlp()
            sys.exit()
        elif opt in ("-f", "--file"):
            filename = arg
        elif opt in ("-d", "--destination"):
            destination = arg
        elif opt in ("-o", "--overwrite"):
            overwrite = True
        elif opt in ("-k", "--key"):
            setting = arg
        elif opt in ("-v", "--value"):
            value = arg
        elif opt in ("-t", "--type"):
            type = arg
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-m", "--model"):
            model = arg
        elif opt in ("-i", "--info"):
            info = True
        elif opt in ("-c", "--commandfile"):
            commandfile = arg
        elif opt in ("-s", "--shell"):
            shell_mode = True
        else:
            print("Unknown option '{}'".format(opt))
            print(USAGE)
            sys.exit(2)

    cmds = []
    if destination:
        Command.DESTINATION = destination
        Brres.DESTINATION = destination
    if overwrite:
        Command.OVERWRITE = overwrite
        Brres.OVERWRITE = overwrite
    if setting:
        cmd = "set " + type + setting + ":" + value + " for " + name
        if model:
            cmd += " model " + model
        cmds.append(Command(cmd))
        if info:
            cmds.append(Command("info"))
    if commandfile:
        filecmds = load_commandfile(commandfile)
        cmds = cmds + filecmds
    if info:
        cmd = "info " + type + setting + " for " + name
        cmds.append(Command(cmd))
    if filename:
        Command.updateFile(filename)
    # Load presets
    preset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presets.txt')
    if os.path.exists(preset_path):
        load_commandfile(preset_path)

    # Run Commands
    if not cmds and not shell_mode:
        print(USAGE)
    else:
        run_commands(cmds)
    if shell_mode:
        Shell().cmdloop('Interactive shell started...')
    # cleanup
    for file in Command.ACTIVE_FILES:
        file.close()


if __name__ == "__main__":
    main()
