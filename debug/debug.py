import os
import sys
from fnmatch import fnmatch


def should_replace(is_commented, enable_comments):
    return is_commented and not enable_comments or not is_commented and enable_comments


def enable_debug(file, enable=True):
    lines = []
    start_debug = replaced_line = False
    with open(file) as f:
        for line in f.readlines():
            replace = False
            s_upper = line.strip()
            s = s_upper.lower()
            if s.startswith('#- debug') or s.startswith('# - debug'):
                start_debug = True
            elif s.find('#- debug') > 0 or s.find('# - debug') > 0:
                replace = should_replace(s.startswith('#'), not enable)
            elif s.startswith('#- end debug') or s.startswith('# - end debug'):
                start_debug = False
            elif start_debug and should_replace(s.startswith('#'), not enable):
                replace = True
            if not replace:
                lines.append(line)
            else:
                if enable:
                    rep = '#'
                    if len(s) > 1 and s[1] == ' ':
                        rep += ' '
                    lines.append(line.replace(rep, '', 1))
                else:
                    insert_at = line.find(s_upper)
                    if insert_at == -1:
                        raise ValueError(insert_at)
                    lines.append(line[:insert_at] + '# ' + line[insert_at:])
                replaced_line = True
    if replaced_line:
        with open(file, 'w') as f:
            f.writelines(lines)
        s = 'enabled' if enable else 'disabled'
        print('{} debugging in {}'.format(s, file))


def walk_dir(dir, filter):
    for root, subdirs, files in os.walk(dir):
        for item in files:
            if fnmatch(item, filter):
                yield os.path.join(root, item)
        for sub in subdirs:
            if sub != '__pycache__':
                yield from walk_dir(os.path.join(root, sub), filter)  # recurse


def main(argv):
    enable_debugging = False
    disable_debugging = False
    files = []
    directories = []
    for arg in argv:
        argl = arg.lower()
        if argl == 'enable':
            enable_debugging = True
        elif argl == 'disable':
            disable_debugging = True
        elif os.path.exists(arg):
            if os.path.isdir(arg):
                directories.append(arg)
            else:
                files.append(arg)
    if not enable_debugging and not disable_debugging:
        enable_debugging = True # default
    if enable_debugging and disable_debugging:
        print('Must specify "enable" or "disable"')
    if not files and not directories:
        path = os.path.abspath(os.getcwd())
        if os.path.basename(path) == 'debug':
            path = os.path.dirname(path)
        directories.append(path)
    for f in files:
        print('Searching for {}'.format(f))
        if not os.path.exists(f):
            print('Failed to find {}'.format(f))
        enable_debug(f, enable_debugging)
    for d in directories:
        print('Searching in {}'.format(d))
        for f in walk_dir(d, '*.py'):
            enable_debug(f, enable_debugging)


if __name__ == '__main__':
    main(sys.argv[1:])
