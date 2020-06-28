""" Matching and miscellaneous functions, and clipable interface """

import re
from fuzzywuzzy import fuzz

BOOLABLE = ["False", "True"]


def fuzzy_match(text, group, acceptable_ratio=84):
    bssf = None
    best_ratio = 0
    lower = text.lower()
    for x in group:
        r = fuzz.ratio(lower, x.name.lower())
        if r > best_ratio:
            best_ratio = r
            bssf = x
    return bssf if best_ratio > acceptable_ratio else None


def fuzzy_strings(text, strings, acceptable_ratio=50):
    """Same as fuzzy_match except expects group of strings"""
    bssf = None
    best_ratio = 0
    lower = text.lower()
    for x in strings:
        r = fuzz.ratio(lower, x.lower())
        if r > best_ratio:
            best_ratio = r
            bssf = x
    return bssf if best_ratio > acceptable_ratio else None


class Clipable:
    """Clipable interface"""
    # ---------------------------------------------- CLIPBOARD -------------------------------------------
    def clip(self, clipboard):
        clipboard[self.name] = self

    def clip_find(self, clipboard):
        return clipboard.get(self.name)

    def paste(self, item):
        pass


def info_default(obj, prefix='', key=None, indentation=0):
    s = '  ' * indentation if indentation else ''
    if key:
        print('{}{}: {}:{}'.format(s, prefix, key, obj[key]))
    else:
        s += prefix + ': '
        for x in obj.SETTINGS:
            s += x + ':' + str(obj[x]) + ', '
        print(s[:-2])


def splitKeyVal(value, default_key='0'):
    i = value.find(':')
    if i >= 0:
        key = value[:i]
        try:
            value = value[i + 1:]
        except IndexError:
            raise ValueError('syntax error "{}", val required after colon'.format(value))
    else:
        key = default_key
    return key, value


def validFloat(str, min, max):
    f = float(str)
    if not min <= f < max:
        raise ValueError("{} is out of range, min: {} max: {}".format(str, min, max))
    return f


def validInt(str, min, max):
    """ checks if a string is a valid integer """
    i = int(str)
    if not min <= i < max:
        raise ValueError("{} is out of range, min: {} max: {}".format(str, min, max))
    return i


def validBool(str):
    """ Checks if its a valid boolean string """
    if str == "false" or not str or str == "0" or str == "disable" or str == "none":
        return False
    elif str == "true" or str == "1" or str == "enable":
        return True
    raise ValueError("Not a boolean '" + str + "', expected true|false")


# finds index of item, if it is equal to compare index returns -1
# raises error if not found
def indexListItem(list, item, compareIndex=-2):
    """ checks for item in list, indexing it """
    for i in range(len(list)):
        if list[i] == item:
            if i != compareIndex:
                return i
            else:
                return -1
    raise ValueError("Invalid setting '" + item + "', Options are: " + str(list))


def parseValStr(value):
    """ Parses tuple formed string with no spaces """
    return value.strip('()').split(",")


# finds a name in group, group instances must have .name
# possible todo, fuzzy searching?
def findAll(name, group):
    """ Finds all names matching in a group, either by direct matching or regex if direct fails."""
    if not name or name == "*":
        return group
    items = []
    # direct matching?
    for item in group:
        if item.name == name:
            items.append(item)
    if not items:
        try:
            regex = re.compile(name)
            for item in group:
                if regex.search(item.name):
                    items.append(item)
        except re.error:
            pass
    return items


def matches(regexname, name):
    """ checks if two names match by direct or regex matching """
    if not regexname or regexname == "*":
        return True
    if regexname == name:
        return True
    try:
        result = re.search(regexname, name)
        if result:
            return True
    except re.error:
        pass
    return False
