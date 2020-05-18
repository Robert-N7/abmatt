# ---------------------------------------------------------------------------
# Command class and functions
# ---------------------------------------------------------------------------
import os
import re
from material import *
from layer import *
from brres import Brres
import fnmatch
import sys

class Command:
    COMMANDS = ["set", "info"]
    def __init__(self, cmd, key, value, name, file, model, material):
        self.cmd = cmd
        self.key = key
        self.value = value
        self.name = name
        self.filename = file
        self.modelname = model
        self.materialname = material

def validate_cmds(commandlist, destination):
    if not commandlist:
        print("No commands detected")
        return False
    file = ""
    count = 0
    for cmd in commandlist:
        if cmd.key:
            cmd.key = cmd.key.lower()
        cmd.cmd = cmd.cmd.lower()
        if cmd.value:
            cmd.value = cmd.value.lower()
        if count == 0 and not cmd.filename:
            print("File is required to run commands!")
            return False
        count += 1
        try:
            i = cmd.COMMANDS.index(cmd.cmd)
            if i == 0:
                if not cmd.key:
                    print("Key is required for command 'set'")
                    return False
                elif not cmd.key in Material.SETTINGS and not cmd.key in Layer.SETTINGS:
                    print("Unknown Key {}".format(cmd.key))
                    return False
        except ValueError:
            print("Unknown command {}".format(cmd.cmd))
            return False
        if cmd.filename:
            files = getFiles(cmd.filename)
            if not files: # could possibly ignore error here for wildcard patterns?
                print("The file '{}' does not exist".format( cmd.filename))
                return False
            elif destination and len(files) > 1 or file and files[0] != file:
                print("Error: Multiple files for single destination!")
                print("Specify single file and destination, or no destination with overwrite option.")
                return False
            elif not file:
                file = files[0]
    return count


def run_commands(commandlist, destination, overwrite):
    if not validate_cmds(commandlist, destination):
        sys.exit(1)
    files = {}
    for cmd in commandlist:
        if cmd.filename:
            filenames = getFiles(cmd.filename)
            closeFiles(filenames, files, destination, overwrite)
            openFiles(filenames, files)
        for index in files:
            files[index].parseCommand(cmd)
    closeFiles(None, files, destination, overwrite)


def load_commandfile(filename):
    if not os.path.exists(filename):
        print("No such file {}".format(filename))
        exit(2)
    f = open(filename, "r")
    lines = f.readlines()
    regex = re.compile("(?P<cmd>\w+)\s*(for\s+(?P<item>\S+)|(?P<key>\w+)?(\s*:(?P<value>\w+))?(\s+for\s+(?P<item2>\S+))?)(\s+in(\s+file\s+(?P<fname>\S+))?(\s+model\s+(?P<modelname>\S+))?(\s+material\s+(?P<matname>\S+))?)?$")
    commands = []
    for line in lines:
        if line[0].isalpha():
            match = regex.match(line)
            if match:
                item = match["item"] if match["item"] else match["item2"]
                commands.append(Command(match["cmd"], match["key"], match["value"], item, match["fname"], match["modelname"], match["matname"]))
            else:
                print("Failed to parse line: '{}'".format(line))
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
    for f in filenames:
        if not f in files:
            brres = Brres(f)
            files[f] = brres

def closeFiles(excludenames, openfiles, destination, overwrite):
    for fname in openfiles:
        if not excludenames or not fname in excludenames:
            openfiles[fname].save(destination, overwrite)
