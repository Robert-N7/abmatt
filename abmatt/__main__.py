#!/usr/bin/env python3
"""
ANoob's Brres Material Editor
For editing Mario Kart Wii files
"""
import sys

import load_config
from load_config import load_config, parse_args


def main():
    """ Main """
    argv = sys.argv[1:]
    if not argv:
        print(load_config.USAGE)
        sys.exit(0)
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = __file__
    files = parse_args(argv, base_path)
    # cleanup
    for file in files.values():
        file.close()


if __name__ == "__main__":
    main()
