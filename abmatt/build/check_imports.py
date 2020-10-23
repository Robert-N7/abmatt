import os
import re

class ImportChecker:
    def __init__(self, root):
        self.root = root

    def trace_parent(self, module):
        parent = self.parents.get(module)
        if parent:
            return self.trace_parent(parent) + '.' + module
        return module

    def convert_relative_import(self, line, top_module):
        x = self.trace_parent(top_module.strip('.'))
        return line.replace(top_module, x, 1)


    def check_file(self, file_path, package_modules):
        total_warns = 0
        with open(file_path) as f:
            data = f.readlines()
            new_data = []
            for i in range(len(data)):
                line = data[i]
                match = re.search('(from (?P<from>\.?\w+)(\.\w+)* )?import (?P<imported>\w+).*', line)
                new_line = None
                if match:
                    d = match.groupdict()
                    imported = d.get('from')
                    if not imported:
                        imported = d.get('imported')
                    # imported = imported.strip('.')
                    if imported != 'abmatt':
                        if imported in package_modules:
                            print(f'WARN: relative import line {i} in {file_path}: {line}')
                            new_line = self.convert_relative_import(line, imported)
                            total_warns += 1
                if new_line:
                    new_data.append(new_line)
                else:
                    new_data.append(line)
        if total_warns:
            with open(file_path, 'w') as f:
                f.write(''.join(new_data))
        return total_warns

    @staticmethod
    def is_package(folder):
        return os.path.exists(os.path.join(folder, '__init__.py'))


    def gather_modules(self, root_path, parents):
        modules = []
        module_file_paths = []
        parent = os.path.basename(root_path)
        for file in os.scandir(root_path):
            if file.is_dir():
                if self.is_package(file.path):
                    module = os.path.basename(file.path)
                    modules.append(module)
                    if module not in parents:
                        parents[module] = parent
                    sub_modules, sub_file_paths = self.gather_modules(file.path, parents)
                    modules.extend(sub_modules)
                    module_file_paths.extend(sub_file_paths)
            else:
                base_name = os.path.basename(file.path)
                if base_name.endswith('.py'):
                    module = base_name[:-3]
                    modules.append(module)
                    module_file_paths.append(file.path)
                    if module not in parents:
                        parents[module] = parent
        return modules, module_file_paths


    def check_imports(self):
        total_warnings = 0
        self.parents = {}
        modules, module_paths = self.gather_modules(self.root, self.parents)
        for path in module_paths:
            total_warnings += self.check_file(path, modules)
        if total_warnings:
            print(f'{total_warnings} relative import warnings')
        else:
            print('Imports are OK')


if __name__ == '__main__':
    x = ImportChecker(os.path.dirname(os.path.dirname(__file__)))
    x.check_imports()
