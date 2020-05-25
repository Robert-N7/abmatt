''' Matching functions '''

import re
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
