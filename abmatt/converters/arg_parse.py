import os
import sys


def arg_parse(args):
    def parse_failed(err):
        usage = 'Usage: convert <file_in> [<file_out>]'
        print(err)
        print(usage)
        sys.exit(1)

    if not len(args):
        parse_failed('Not enough arguments!')
    in_file = args.pop(0)
    if not os.path.exists(in_file):
        parse_failed('File {} does not exist!'.format(in_file))
    destination = None
    if len(args):
        next = args.pop(0)
        if next in ('to', '-d', '--destination'):
            if not len(args):
                parse_failed('Destination required after -d flag!')
            destination = args.pop(0)
        else:
            destination = next
    return in_file, destination
