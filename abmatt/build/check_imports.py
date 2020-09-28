import os
import re


def check_file(file_path, package_modules):
    total_warns = 0
    with open(file_path) as f:
        data = f.readlines()
        for i in range(len(data)):
            line = data[i]
            match = re.search('from (\.?\w+)(\.\w+)* import', line)
            if match:
                group = match.group(1)
                imported = group.strip('.')
                if imported != 'abmatt':
                    if imported in package_modules:
                        print(f'WARN: relative import line {i} in {file_path}: {line}')
                        total_warns += 1
    return total_warns


def is_package(folder):
    return os.path.exists(os.path.join(folder, '__init__.py'))


def gather_modules(root_path):
    modules = []
    module_file_paths = []
    for file in os.scandir(root_path):
        if file.is_dir():
            if is_package(file.path):
                modules.append(os.path.basename(file.path))
                sub_modules, sub_file_paths = gather_modules(file.path)
                modules.extend(sub_modules)
                module_file_paths.extend(sub_file_paths)
        else:
            base_name = os.path.basename(file.path)
            if base_name.endswith('.py'):
                modules.append(base_name[:-3])
                module_file_paths.append(file.path)
    return modules, module_file_paths


def check_imports(root):
    total_warnings = 0
    modules, module_paths = gather_modules(root)
    for path in module_paths:
        total_warnings += check_file(path, modules)
    if total_warnings:
        print(f'{total_warnings} relative import warnings')
    else:
        print('Imports are OK')


if __name__ == '__main__':
    check_imports(os.path.dirname(os.path.dirname(__file__)))
