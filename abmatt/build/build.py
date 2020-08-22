import os
import shutil
import sys
import platform
from abmatt.config import Config


def main(args):
    # update version/bit_width
    config_path = 'config.txt'
    if not os.path.exists(config_path):
        print('No configuration file!')
        sys.exit(1)
    c = Config(config_path)
    os.chdir('../dist')
    os.system('update_version.py')
    # read configuration
    bit_width = c['bit_width']
    version = c['version']
    interpreter = c['64-bit'] if bit_width == 'x64' else c['32-bit']
    name = c['build_name']
    build_type = c['build_type']
    # build
    clean(name, [name + '.exe', name])
    my_platform = platform.system().lower()
    out_file, is_dir = build(name, build_type, interpreter, my_platform)
    if not out_file:
        sys.exit(1)
    dist_dir = 'abmatt_' + my_platform + '-' + platform.release() + '_' \
               + bit_width + '-' + version
    # clean
    clean(dist_dir, (dist_dir + '.zip', dist_dir + '.tar.gz', 'dist_dir'))
    # dist
    if not make_distribution(dist_dir, my_platform, out_file, is_dir):
        sys.exit(1)


def tar(path):
    return not os.system('tar -czvf ' + path + '.tar.gz ' + path)


def zip(path):
    return not os.system('7z a -tzip ' + path + '.zip ' + path)


def make_distribution(dir, platform, binary_path, binary_path_is_dir):
    os.mkdir(dir)
    os.chdir(dir)
    os.mkdir('etc')
    os.chdir('etc')
    os.mkdir('abmatt')
    os.chdir('../..')
    shutil.copy('../../LICENSE', dir)
    shutil.copy('../../README.md', dir)
    etc = dir + '/etc/abmatt'
    shutil.copy('../presets.txt', etc)
    shutil.copy('../config.conf', etc)
    dest_dir = os.path.join(dir, 'bin')
    bin_dir, base_name = os.path.split(binary_path)
    exe = os.path.join(dest_dir, 'abmatt')
    if 'exe' in base_name:
        exe += '.exe'
    if binary_path_is_dir:
        shutil.copytree(bin_dir, dest_dir)
        shutil.move(os.path.join(dest_dir, base_name), exe)
    else:
        os.mkdir(dest_dir)
        shutil.copy(binary_path, exe)
    # platform specific files
    if platform == 'windows':
        shutil.copy('./install-win.txt', dir)
        shutil.copy('./make_installer.nsi', dir)
        os.chdir(dir)
        if os.system('makensis make_installer.nsi'):
            return False
        os.remove('./make_installer.nsi')
        shutil.rmtree('etc')
        shutil.rmtree('bin')
        os.chdir('..')
        if not zip(dir):
            return False
    else:
        shutil.copy('./install.sh', dir)
        shutil.copy('./uninstall.sh', dir)
        shutil.copy('./install-ubu.txt', os.path.join(dir, 'install.txt'))
        os.chdir('..')
        if not tar(dir):
            return False
    return True


def clean(folder, files):
    if os.path.exists(folder) and os.path.isdir(folder):
        shutil.rmtree(folder)
    for x in files:
        if os.path.exists(x) and os.path.isfile(x):
            os.remove(x)


def build(name, build_type, interpreter, platform):
    output = None
    os.chdir('..')
    for x in os.listdir():
        if x.endswith('.pyc'):
            os.remove(x)
    if build_type == 'auto':
        output_type = '--onedir' if platform == 'windows' else 'onefile'
    else:
        output_type = '--' + build_type
    is_dir = True if 'onedir' in output_type else False
    params = '-y __main__.py -p ../../venv/Lib/site-packages --name ' + name + ' ' + output_type
    result = os.system(interpreter + ' -m PyInstaller ' + params)
    os.chdir('dist')
    if not result:
        output = name if not is_dir else name + '/' + name
        if not os.path.exists(output) or os.path.isdir(output):
            output += '.exe'
            if not os.path.exists(output):
                print('Unable to find PyInstaller output file!')
                sys.exit(1)
        result = os.system(os.path.join(os.getcwd(), output) + ' -b ../../brres_files/beginner_course.brres -d ../../brres_files/test.brres -o')
        if not result:
            return output, is_dir
    return None, is_dir


if __name__ == '__main__':
    main(sys.argv[1:])
