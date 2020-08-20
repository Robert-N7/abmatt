#!/usr/bin/python

# Updates the version throughout files
import os
import re
import sys

def update_version(version):
    version_files = ['../../setup.py', 'install-ubu.txt', 'install-win.txt', '../__main__.py', 'Makefile',
                     'update_version.py', 'make_installer.nsi']
    # version_files = ['test.txt']
    rex = re.compile("(version\s*(\:|\=)?\s*(\"|\')?)\d+\.\d+\.\d+", re.IGNORECASE)
    replacement = '\g<1>' + version
    count = 0
    for x in version_files:
        if os.path.exists(x):
            with open(x) as file:
                fixed = rex.sub(replacement, file.read())
            with open(x, 'w') as file:
                file.write(fixed)
                count += 1
    print('Updated version {} in {} files'.format(version, count))
    with open('version', 'w') as f:
        f.write(version)


def update_bit_width(str_width, is_64_bit):
    with open('bit_width', 'w') as f:
        f.write(str_width)
    filename = 'make_installer.nsi'
    new_data = data = None
    replacement = 'InstallDir "$PROGRAMFILES' + str_width + '\\abmatt"'
    with open(filename, 'r') as f:
        data = f.read()
        new_data = re.sub(r'InstallDir "\$PROGRAMFILES\d*\\abmatt"', data, replacement)
    if new_data:
        with open(filename, 'w') as f:
            f.write(new_data)


def main(version, bit_width):
    try:
        width = int(bit_width)
        is_64_bit = ['32', '64'].index(width)
        update_bit_width(bit_width, is_64_bit)
    except ValueError:
        print('Bit width {} not an int'.format(bit_width))
        exit(1)
    update_version(version)

if __name__ == '__main__':
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        with open('version') as f:
            version = f.read()
    if not version:
        print('No version detected! Run ./update_version.py x.x.x')
        sys.exit(1)
    with open('bit_width') as f:
        bit_width = f.read()
    main(version, bit_width)
