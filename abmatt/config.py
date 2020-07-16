#!/usr/bin/python
"""For reading configuration file"""
import os


def parse_line(line):
    if line:
        comment = line.find('#')
        if comment >= 0:
            line = line[:comment]
        split_line = line.split('=', 1)
        if len(split_line) > 1:
            return [x.strip() for x in split_line]
    return None


class Config:
    def __init__(self, filename):
        self.config = {}
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for cnt, line, in enumerate(f):
                    result = parse_line(line)
                    if result is not None:
                        self.config[result[0]] = result[1]

    def __getitem__(self, item):
        return self.config.get(item)

    def __setitem__(self, key, value):
        self.config[key] = value
