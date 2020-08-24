import os
import sys


class Path:
    def __init__(self, path):
        self.dir, filename = os.path.split(path)
        self.filename, self.ext = os.path.splitext(filename)

    def get_path(self):
        return os.path.join(self.dir, self.filename + self.ext)


def arg_parse(args):
    def parse_failed(err):
        usage = 'Usage: convert <file_in> [<file_out>] [--overwrite]'
        print(err)
        print(usage)
        sys.exit(1)

    overwrite = False
    destination = None
    if not len(args):
        parse_failed('Not enough arguments!')
    in_file = args.pop(0)
    if not os.path.exists(in_file):
        parse_failed('File {} does not exist!'.format(in_file))
    in_file = Path(in_file)
    if len(args):
        next = args.pop(0)
        if next in ('to', '-d', '--destination'):
            if not len(args):
                parse_failed('Destination required after -d flag!')
            destination = args.pop(0)
        elif next in ('-o', '--overwrite'):
            overwrite = True
        else:
            destination = next
        if len(args) and next in ('-o', '--overwrite'):
            overwrite = True
    if not destination:
        dest_file = in_file.filename + '.brres' if in_file.ext != '.brres' else in_file.filename
        destination = os.path.join(in_file.dir, dest_file)
    return in_file, Path(destination), overwrite
