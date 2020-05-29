''' Matching functions '''

import re
BOOLABLE = ["False", "True"]

def validFloat(str, min, max):
    f = float(str)
    if not min <= i < max:
        raise ValueError("{} is out of range, min: {} max: {}".format(str, min, max))
    return f

def validInt(str, min, max):
    ''' checks if a string is a valid integer '''
    i = int(str)
    if not min <= i < max:
        raise ValueError("{} is out of range, min: {} max: {}".format(str, min, max))
    return i

def validBool(str):
    ''' Checks if its a valid boolean string '''
    if str == "false" or not str or str == "0" or str == "disable":
        return False
    elif str == "true" or str == "1" or str == "enable":
        return True
    raise ValueError("Not a boolean '" + str + "', expected true|false")

# finds index of item, if it is equal to compare index returns -1
# raises error if not found
def indexListItem(list, item, compareIndex = -2):
    ''' checks for item in list, indexing it '''
    for i in range(len(list)):
        if list[i] == item:
            if i != compareIndex:
                return i
            else:
                return -1
    raise ValueError("Invalid setting '" + item + "', Options are: " + str(list))

def parseValStr(value):
    ''' Parses tuple formed string with no spaces '''
    if value[0] == "(" and value[-1] == ")":
        value = value[1:-1]
    return value.split(",")


# finds a name in group, group instances must have .name
def findAll(name, group):
    ''' Finds all names matching in a group, either by direct matching or regex if direct fails.'''
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
    ''' checks if two names match by direct or regex matching '''
    if not regexname or regexname == "*":
        return True
    if regexname == name:
        return True
    try:
        result = re.match(regexname, name)
        if result:
            return True
    except re.error:
        pass
    return False