import os
import shutil
import sys
import platform
from abmatt.config import Config


def main(args):
    # update version/bit_width
    c = Config('config.txt')
    os.chdir('../dist')
    os.system('update_version.py')
    # read configuration
    bit_width = c['bit_width']
    version = c['version']
    interpreter = c['64-bit'] if bit_width == 'x64' else c['32-bit']
    # build
    if not build(interpreter):
        sys.exit(1)
    my_platform = platform.system().lower()
    dist_dir = 'abmatt_' + my_platform + '-' + platform.release() + '_' \
               + bit_width + '-' + version
    # clean
    clean(dist_dir, (dist_dir + '.zip', dist_dir + '.tar.gz', 'dist_dir'))
    if not make_distribution(dist_dir, my_platform):
        sys.exit(1)


def make_distribution(dir, platform):
    with open('dist_dir', 'w') as f:
        f.write(dir)
    err = os.system('make ' + platform)
    return not err


def clean(folder, files):
    if os.path.exists(folder):
        shutil.rmtree(folder)
    for x in files:
        if os.path.exists(x):
            os.remove(x)


def build(interpreter):
    output = None
    os.chdir('..')
    name = 'abmatt'
    result = os.system(interpreter + ' -m PyInstaller -y -F __main__.py --onedir --name ' + name)
    os.chdir('dist')
    if not result:
        output = os.path.join(name, name)
        if not os.path.exists(output):
            output += '.exe'
            if not os.path.exists(output):
                print('Unable to find PyInstaller output file!')
                sys.exit(1)
        result = os.system(output + ' -b ../../brres_files/beginner_course.brres -d ../../brres_files/test.brres -o')
        if not result:
            return output
    return 0


if __name__ == '__main__':
    main(sys.argv[1:])
