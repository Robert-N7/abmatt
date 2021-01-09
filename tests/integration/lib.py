import os
import subprocess
import sys
import colorama

colorama.init()

class bcolors:
    HEADER = '\033[35m'
    OKBLUE = '\033[34m'
    OKGREEN = '\033[32m'
    WARNING = '\033[33m'
    FAIL = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class IntegTest:
    def __init__(self, args):
        self.loudness = '1'
        for i in range(len(args)):
            arg = args[i]
            if arg in ('-l', '--loudness'):
                self.loudness = args[i + 1]
        self.__run_tests(args)

    def __run_tests(self, args):
        run_all = False if args else True
        test_total = tests_passed = 0
        public_method_names = [method for method in dir(self) if callable(getattr(self, method)) if \
                               not method.startswith('_')]  # 'private' methods start from _
        for method in public_method_names:
            if run_all or method in args:
                print(f'{bcolors.OKGREEN}Running {method}{bcolors.ENDC}')
                result = getattr(self, method)()
                if result:
                    tests_passed += 1
                else:
                    print(f'{bcolors.FAIL}{method} failed.{bcolors.ENDC}')
                test_total += 1
        tests_failed = test_total - tests_passed
        if tests_failed:
            print(f'{bcolors.FAIL}{tests_passed}/{test_total} tests passed.{bcolors.ENDC}')
        else:
            print(f'{bcolors.OKBLUE}{tests_passed}/{test_total} tests passed.{bcolors.ENDC}')
        if tests_failed:
            sys.exit(tests_failed)
        return tests_failed

    def _abmatt(self, params):
        params += ' -g -l ' + self.loudness
        p = [sys.executable, './abmatt/__main__.py']
        p.extend(params.split(' '))
        result = subprocess.call(p, cwd=os.path.dirname(os.path.dirname(os.getcwd())))
        return not result

    def _abmatt_simple(self, params):
        return self._abmatt(params + ' -b brres_files/simple.brres -d brres_files/test.brres -o')
