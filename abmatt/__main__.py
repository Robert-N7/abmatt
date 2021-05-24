#!/usr/bin/env python3
"""
ANoob's Brres Material Editor
For editing Mario Kart Wii files
"""
import os.path
import sys

from abmatt import load_config


def main():
    """ Main """
    argv = sys.argv[1:]
    if not argv:
        print(load_config.USAGE)
        sys.exit(0)
    if getattr(sys, 'frozen', False):
        base_path = sys.executable
    else:
        base_path = os.path.abspath(__file__)
    files = load_config.parse_args(argv, base_path)
    # cleanup
    for file in files:
        file.close()


if __name__ == "__main__":
    main()
