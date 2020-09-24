import os
import subprocess
import sys


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
    def __init__(self):
        self.__run_tests()

    def __run_tests(self):
        test_total = tests_passed = 0
        public_method_names = [method for method in dir(self) if callable(getattr(self, method)) if \
                               not method.startswith('_')]  # 'private' methods start from _
        for method in public_method_names:
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


def abmatt(params):
    params += ' -g -l 0'
    p = [sys.executable, './abmatt/__main__.py']
    p.extend(params.split(' '))
    result = subprocess.call(p, cwd=os.path.dirname(os.path.dirname(os.getcwd())))
    return not result


def abmatt_desert(params):
    return abmatt(params + ' -b brres_files/desert_course.brres -d brres_files/test.brres -o')


def abmatt_beginner(params):
    return abmatt(params + ' -b brres_files/beginner_course.brres -d brres_files/test.brres -o')


def abmatt_water(params):
    return abmatt(params + ' -b brres_files/water_course.brres -d brres_files/test.brres -o')
