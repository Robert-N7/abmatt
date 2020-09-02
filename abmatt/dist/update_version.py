#!/usr/bin/python

# Updates the version throughout files
import os
import re
import sys

from config import Config


def get_last_update(version_file):
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read()


def update_version(version):
    version_file = 'version'
    if version == get_last_update(version_file):
        print('Version already up to date')
        return 0
    version_files = ['../../setup.py', 'install-ubu.txt', 'install-win.txt', '../__main__.py', 'Makefile',
                     'update_version.py', 'make_installer.nsi', '../converters/obj.py']
    # version_files = ['test.txt']
    rex = re.compile("(v(ersion)?\s*(\:|\=)?\s*(\"|\')?)\d+\.\d+\.\d+", re.IGNORECASE)
    replacement = '\g<1>' + version
    count = 0
    for x in version_files:
        if os.path.exists(x):
            with open(x) as file:
                fixed = rex.sub(replacement, file.read())
            with open(x, 'w') as file:
                file.write(fixed)
                count += 1
    with open(version_file, 'w') as f:
        f.write(version)
    return count


def update_bit_width(is_64_bit):
    filename = 'make_installer.nsi'
    new_data = data = None
    str_width = '64' if is_64_bit else '32'
    with open(filename, 'r') as f:
        data = f.read()
        new_data, found = re.subn(r'^(InstallDir "\$PROGRAMFILES)\d*(\\abmatt")', '\g<1>' + str_width + '\g<2>', data,
                                  1, re.MULTILINE)
        if not found:
            print('Failed to replace bit width in installer')
    if new_data:
        with open(filename, 'w') as f:
            f.write(new_data)


def main(args):
    usage = 'update_version.py [version [bit_width]]'
    bit_width = version = None
    c = Config('../build/config.txt')
    if len(args):
        version = args.pop(0)
        if not re.match(r'\d+\.\d+\.\d+', version):
            print('Invalid version format {}'.format(version))
            sys.exit(1)
        c['version'] = version
    else:
        version = c['version']
    if not version:
        print('No version detected!')
        print(usage)
        sys.exit(1)
    if len(args):
        bit_width = args.pop(0)
        is_64_bit = ['x86', 'x64'].index(bit_width)
        c['bit_width'] = bit_width
    else:
        bit_width = c['bit_width']
        is_64_bit = ['x86', 'x64'].index(bit_width)
    if not bit_width:
        print('Bit width not set!')
        print(usage)
        sys.exit(1)
    update_bit_width(is_64_bit)
    count = update_version(version)
    print('Updated version {} {} in {} files'.format(version, bit_width, count))


if __name__ == '__main__':
    main(sys.argv[1:])
