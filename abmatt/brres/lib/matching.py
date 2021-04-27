""" Matching and miscellaneous functions, and clipable interface """

import re

BOOLABLE = ["False", "True"]


def fuzzy_match(text, group, acceptable_ratio=84):
    from fuzzywuzzy import fuzz
    bssf = None
    best_ratio = 0
    lower = text.lower()
    for x in group:
        r = fuzz.ratio(lower, x.name.lower())
        if r > best_ratio:
            best_ratio = r
            bssf = x
    if best_ratio < acceptable_ratio and len(lower) > 2:
        for x in group:
            r = fuzz.partial_ratio(lower, x.name.lower())
            if r > best_ratio:
                best_ratio = r
                bssf = x

    return bssf if best_ratio >= acceptable_ratio else None


def fuzzy_strings(text, strings, acceptable_ratio=84):
    """Same as fuzzy_match except expects group of strings"""
    from fuzzywuzzy import fuzz
    bssf = None
    best_ratio = 0
    lower = text.lower()
    for x in strings:
        r = fuzz.ratio(lower, x.lower())
        if r > best_ratio:
            best_ratio = r
            bssf = x
    return bssf if best_ratio > acceptable_ratio else None


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


def validInt(str, min=-0x7fffffff, max=0x7fffffff):
    """ checks if a string is a valid integer """
    i = int(str)
    if not min <= i < max:
        raise ValueError("{} is out of range, min: {} max: {}".format(str, min, max))
    return i


def it_eq(x, y):
    """determines if iterable is equal"""
    x_type = type(x)
    y_type = type(y)
    if x_type != tuple and x_type != list or y_type != tuple and y_type != list:
        return x == y   # default comparison
    if len(x) != len(y):
        return False
    # recursively compare, in case of nested iterables
    for i in range(len(x)):
        if not it_eq(x[i], y[i]):
            return False
    return True


def parse_color(color_str):
    """parses color string"""
    if not color_str:
        return 0, 0, 0, 0
    color_str = color_str.strip('()')
    colors = color_str.split(',')
    if len(colors) < 4:
        if color_str == '0':
            return 0, 0, 0, 0
        return None
    intVals = []
    for x in colors:
        i = int(x)
        if not 0 <= i <= 255:
            raise ValueError(f'{color_str} not a valid color string!')
        intVals.append(i)
    return intVals


def validBool(str):
    """ Checks if its a valid boolean string """
    str = str.lower()
    if str == "false" or not str or str == "0" or "disable" in str or str == "none":
        return False
    elif str == "true" or str == "1" or "enable" in str:
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
    """ Parses tuple/list formed string"""
    values = value.strip('\'[]()').split(",")
    for i in range(len(values)):
        values[i] = values[i].strip()
    return values


""" Matching class """


class Matching:
    PARTIAL_ON_NONE_FOUND = 2
    PARTIAL_ENABLED = 1
    PARTIAL_DISABLED = 0
    REGEX_ON_NONE_FOUND = 2
    REGEX_ENABLED = 1
    REGEX_DISABLED = 0

    def __init__(self, case_sensitive=True, partial_matching=2, regex_enable=2):
        self.case_sensitive = case_sensitive
        self.partial_matching = partial_matching
        self.regex_enable = regex_enable
        self.update()

    def update(self):
        if self.partial_matching == 1:
            if self.case_sensitive:
                self.direct_group_function = self.match_group_partial_insensitive
                self.regex_group_function = self.regex_group_partial_insensitive
            else:
                self.direct_group_function = self.match_group_partial_sensitive
                self.regex_group_function = self.regex_group_partial_sensitive
        else:
            if self.case_sensitive:
                self.direct_group_function = self.match_group_full_sensitive
                self.regex_group_function = self.regex_group_full_sensitive
            else:
                self.direct_group_function = self.match_group_full_insensitive
                self.regex_group_function = self.regex_group_full_sensitive

    def set_case_sensitive(self, val):
        try:
            val = validBool(val)
            self.case_sensitive = val
        except ValueError:
            return False
        self.update()
        return True

    def set_partial_matching(self, val):
        if val == 'on_none_found':
            self.partial_matching = self.PARTIAL_ON_NONE_FOUND
        try:
            enable = validBool(val)
            self.partial_matching = 1 if enable else 0
        except ValueError:
            return False
        self.update()
        return True

    def set_regex_enable(self, val):
        if val == 'on_none_found':
            self.regex_enable = self.REGEX_ON_NONE_FOUND
        try:
            enable = validBool(val)
            self.regex_enable = 1 if enable else 0
            self.update()
        except ValueError:
            return False
        return True

    @staticmethod
    def match_group_partial_insensitive(name, group, results):
        name = name.lower()
        for x in group:
            if name in x.name.lower():
                results.append(x)
        return results

    @staticmethod
    def match_group_partial_sensitive(name, group, results):
        for x in group:
            if name in x.name:
                results.append(x)
        return results

    @staticmethod
    def match_group_full_insensitive(name, group, results):
        name = name.lower()
        for x in group:
            if name == x.name.lower():
                results.append(x)
        return results

    @staticmethod
    def match_group_full_sensitive(name, group, results):
        for x in group:
            if name == x.name:
                results.append(x)
        return results

    @staticmethod
    def regex_group_full_insensitive(name, group, results):
        try:
            regex = re.compile(name, re.IGNORECASE)
            for x in group:
                if regex.match(x.name):
                    results.append(x)
        except re.error:
            pass

    @staticmethod
    def regex_group_full_sensitive(name, group, results):
        try:
            regex = re.compile(name)
            for x in group:
                if regex.match(x.name):
                    results.append(x)
        except re.error:
            pass

    @staticmethod
    def regex_group_partial_insensitive(name, group, results):
        try:
            regex = re.compile(name, re.IGNORECASE)
            for x in group:
                if regex.search(x.name):
                    results.append(x)
        except re.error:
            pass

    @staticmethod
    def regex_group_partial_sensitive(name, group, results):
        try:
            regex = re.compile(name)
            for x in group:
                if regex.search(x.name):
                    results.append(x)
        except re.error:
            pass

    # finds a name in group, group instances must have .name
    def findAll(self, name, group):
        """ Finds all names matching in a group, either by direct matching or regex if direct fails."""
        if not name or name == "*" or not group:
            return group
        items = []
        # direct matching
        self.direct_group_function(name, group, items)
        # regex
        if self.regex_enable == self.REGEX_ENABLED or not items and self.regex_enable:
            self.regex_group_function(name, group, items)
            if not items and self.partial_matching == self.PARTIAL_ON_NONE_FOUND:
                if self.case_sensitive:
                    self.regex_group_partial_sensitive(name, group, items)
                else:
                    self.regex_group_partial_insensitive(name, group, items)
        # partial if none found?
        elif not items and self.partial_matching == self.PARTIAL_ON_NONE_FOUND:
            if self.case_sensitive:
                self.match_group_partial_sensitive(name, group, items)
            else:
                self.match_group_partial_insensitive(name, group, items)
        return items


MATCHING = Matching()
