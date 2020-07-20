#!/usr/bin/python

# Updates the version throughout files
import os
import re
import sys

def main(version):
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


version = None
if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    with open('version') as f:
        version = f.read()
if not version:
    print('No version detected! Run ./update_version.py x.x.x')
    sys.exit(1)
main(version)
