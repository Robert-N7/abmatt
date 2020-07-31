import os

from brres.lib.autofix import AUTO_FIXER
from brres.lib.binfile import BinFile


class Node:
    """A node with name and parent"""
    def __init__(self, name, parent, binfile):
        if binfile is not None:
            self.unpack(binfile)
        else:
            self.begin()
        self.parent = parent
        self.name = name

    def begin(self):
        pass

    def unpack(self, binfile):
        raise NotImplementedError()

    def pack(self, binfile):
        raise NotImplementedError()


class Clipable(Node):
    """Clipable interface"""
    OVERWRITE_MODE = False

    @property
    def SETTINGS(self):
        raise NotImplementedError()

    def __init__(self, name, parent, binfile):
        super(Clipable, self).__init__(name, parent, binfile)
        self.is_modified = False

    # ---------------------------------------------- CLIPBOARD -------------------------------------------
    @staticmethod
    def paste_group(paste_group, clip_group):
        for x in clip_group:
            name = x.name
            for y in paste_group:
                if y.name == name:
                    y.paste(x)
                    break

    def set_str(self, key, value):
        raise NotImplementedError()

    def get_str(self, key):
        raise NotImplementedError()

    def clip(self, clipboard):
        clipboard[self.name] = self

    def clip_find(self, clipboard):
        return clipboard.get(self.name)

    def paste(self, item):
        raise NotImplementedError()

    def mark_modified(self):
        if not self.is_modified:
            self.is_modified = self.parent.mark_modified()

    def get_texture_map(self):
        return self.parent.get_texture_map()

    def info(self, key='', indentation_level=0):
        if not key:
            m = max(3, len(self.SETTINGS))
            for i in range(m):
                setting = self.SETTINGS[i]
                key += setting + ':' + self.get_str(setting) + ' '
        else:
            key += ':' + self.get_str(key)
        start = indentation_level * '  '
        print('{}{}> {}'.format(start, self.name, key))
