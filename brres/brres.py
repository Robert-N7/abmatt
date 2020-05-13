#!/usr/bin/python

# -------------------------------------------------------------------
#   lets have fun with python!
# -------------------------------------------------------------------
from unpack import *
from material import *
from pack import *
import re  # yeah regexs are in
import sys, getopt
import os.path

class Brres:
    def __init__(self, fname):
        self.brres = UnpackBrres(fname)
        self.model = self.brres.models[0]
        self.isModified = False

    def save(self, filename, overwrite):
        if not overwrite and os.path.exists(filename):
            print("File '{}' already exists!".format(filename))
            return False
        else:
            packed = PackBrres(self)
            f = open(filename, "wb")
            f.write(f)
            f.close()
            print("Wrote file '{}'".format(filename))
            return True

    def setModel(self, modelname):
        for mdl in self.brres.models:
            if re.search(modelname):
                self.model = mdl
                break

    def parseSetting(self, setting, refname, value):
        pass #todo

    def info(self, name):
        print("Here's some info, you're welcome")
        # todo

    def list_materials(self):
        mats = self.model.mats
        print("Materials:")
        for mat in mats:
            print("\t{}".format(mat.name))

def help():
    print("This is helpful.")
    # todo

def main(argv):
    usage = "brres.py -f <file> [-d <destination> -o -s <setting> -v <value> -n <name> -m <model> -i] "
    try:
        opts, args = getopt.getopt(argv, "hf:d:os:v:n:m:", ["help", "file=", "destination=", "overwrite", "setting=", "value=", "name=", "model=", "info"])
    except: getopt.GetoptError:
        print(usage)
        sys.exit(2)
    filename = ""
    destination = ""
    overwrite = False
    setting = ""
    value = ""
    name = "*"
    model = ""
    info = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            help()
            sys.exit()
        elif opt in ("-f", "--file"):
            filename = arg
        elif opt in ("-d", "--destination"):
            destination = arg
        elif opt in ("-o", "--overwrite"):
            overwrite = True
        elif opt in ("-s", "--setting"):
            setting = arg
        elif opt in ("-v", "--value"):
            value = arg
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-m", "--model"):
            model = arg
        elif opt in ("-i", "--info"):
            info = True
        else:
            print("Unknown option '{}'".format(opt))
            print(usage)
            sys.exit(2)
    if not filename:
        print("Filename is required")
        print(usage)
        sys.exit(2)
    if not os.path.exists(filename):
        print("File '{}' does not exist.".format(filename))
        sys.exit(1)

    b = Brres(filename)
    if model:
        b.setModel(model)
    if setting:
        b.parseSetting(setting, name, value)
    if info or not setting:
        b.info(name)
    if b.isModified or destination:
        b.save(destination, overwrite)
    # interactive mode maybe?


if __name__ == "__main__":
    main(sys.argv[1:])
