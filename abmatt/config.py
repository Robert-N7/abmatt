#!/usr/bin/python
"""For reading configuration file"""
import os
import re


def parse_line(line):
    if line:
        comment = line.find('#')
        if comment >= 0:
            line = line[:comment]
        split_line = line.split('=', 1)
        if len(split_line) > 1:
            return [x.strip().lower() for x in split_line]
    return None


class Config:
    __instance = None

    @staticmethod
    def get_instance(filename=None):
        if Config.__instance is None:
            Config.__instance = Config(filename)
        elif filename:
            Config.__instance.set_file(filename)
        return Config.__instance

    def __init__(self, filename):
        if self.__instance:
            raise RuntimeError('Config is singleton!')
        self.set_file(filename)

    def set_file(self, filename):
        self.config = {}
        self.filename = filename
        if os.path.exists(filename):
            self.filename = os.path.abspath(filename)
            with open(filename, 'r') as f:
                for cnt, line, in enumerate(f):
                    result = parse_line(line)
                    if result is not None:
                        self.config[result[0]] = result[1]

    def __len__(self):
        return len(self.config)

    def __getitem__(self, item):
        return self.config.get(item)

    def __setitem__(self, key, value):
        if value == self.config.get(key):
            return
        self.config[key] = value
        n = None
        has_subbed = False
        with open(self.filename) as f:
            n, has_subbed = re.subn('^(' + key + r'\s*=\s*)[^\n]*', '\g<1>' + value, f.read(), 1, re.MULTILINE)
        if n:
            if not has_subbed:
                n += '\n' + key + ' = ' + value
            with open(self.filename, 'w') as f:
                f.write(n)
