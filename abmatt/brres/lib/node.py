import os
from copy import deepcopy

from abmatt.autofix import AutoFix


def get_name_mapping(group):
    mapper = {}
    for x in group:
        mapper[x.name] = x
    return mapper


def get_item_by_index(group, index):
    try:
        item = group[index]
        if item.index == index:
            return item
    except IndexError:
        pass
    for x in group:
        if x.index == index:
            return x


class Packable:
    def unpack(self, binfile):
        raise NotImplementedError()

    def pack(self, binfile):
        raise NotImplementedError()


class Node:
    """A node with name and parent"""

    def __init__(self, name, parent, binfile=None):
        self.parent = parent
        self.name = name
        if binfile is None:
            self.begin()

    def begin(self):
        pass

    def __deepcopy__(self, memodict=None):
        raise NotImplementedError()

    def __eq__(self, other):
        return other is not None and type(self) == type(other) and self.name == other.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.get_full_path())

    def get_full_path(self):
        return os.path.join(self.parent.get_full_path(), self.name) if self.parent else self.name

    def link_parent(self, parent):
        self.parent = parent


class ClipableObserver:
    """Receives updates from clipable"""

    def on_node_update(self, node):
        pass

    def on_child_update(self, child):  # might not have children
        pass

    def on_rename_update(self, node, old_name):
        pass


class Clipable(Node):
    """Clipable interface"""
    OVERWRITE_MODE = False

    @property
    def SETTINGS(self):
        raise NotImplementedError()

    def __init__(self, name, parent, binfile):
        self.is_modified = False
        self.observers = None  # also make this observable
        super(Clipable, self).__init__(name, parent, binfile)

    def rename(self, name):
        if name != self.name:
            old_name = self.name
            self.name = name
            self.mark_modified(False)
            self.notify_rename(old_name)
            return True
        return False

    # ------------------------------------- OBSERVERS ----------------------------
    def notify_rename(self, old_name):
        if self.observers:
            for x in self.observers:
                x.on_rename_update(self, old_name)
        self.notify_parent_observers()

    def notify_observers(self):
        if self.observers:
            for x in self.observers:
                x.on_node_update(self)
        self.notify_parent_observers()

    def notify_parent_observers(self):
        parent = self.parent
        if parent and parent.observers:
            for x in parent.observers:
                x.on_child_update(self)

    def register_observer(self, observer):
        if self.observers is None:
            self.observers = [observer]
        elif observer not in self.observers:
            self.observers.append(observer)

    def unregister(self, observer):
        try:
            self.observers.remove(observer)
        except ValueError as e:
            pass

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

    def mark_modified(self, notify_observers=True):
        if notify_observers:
            self.notify_observers()
        if not self.is_modified:
            self.is_modified = True
            if self.parent:
                self.parent.mark_modified(False)  # marks parent modified but does not notify

    def _mark_unmodified_group(self, group):
        for x in group:
            x.mark_unmodified()

    def mark_unmodified(self):
        """
        After saving a file, call this on children to reset modification markings
        parents need to call this on their children
        """
        self.is_modified = False

    def get_texture_map(self):
        if self.parent:
            return self.parent.get_texture_map()

    def info(self, key='', indentation_level=0):
        if not key:
            m = max(3, len(self.SETTINGS))
            for i in range(m):
                setting = self.SETTINGS[i]
                key += setting + ':' + self.get_str(setting) + ' '
        else:
            key += ':' + self.get_str(key)
        start = '>' + indentation_level * '  '
        AutoFix.info('{}{}> {}'.format(start, self.name, key), 1)

    def get_full_path(self):
        return os.path.join(self.parent.get_full_path(), self.name)
