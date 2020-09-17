import inspect
import os

from itertools import filter


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def run_tests(obj):
    test_total = tests_passed = 0
    public_method_names = [method for method in dir(obj) if callable(getattr(obj, method)) if \
                           not method.startswith('_')]  # 'private' methods start from _
    for method in public_method_names:
        result = getattr(obj, method)()
        if result:
            tests_passed += 1
        else:
            print(f'{method} failed.')
        test_total += 1
    print('{}/{} tests passed.'.format(tests_passed, test_total))
    tests_failed = test_total - tests_passed
    if tests_failed:
        print(f'{bcolors.WARNING}{test_total - tests_passed} tests failed{bcolors.ENDC}')
    return tests_failed


def abmatt(params):
    os.chdir('../..')
    result = os.system('".\\abmatt\\__main__.py" ' + params)
    os.chdir('tests/integration')
    return not result


def abmatt_desert(params):
    return abmatt(params + ' -b brres_files/desert_course.brres -d brres_files/test.brres -o')


def abmatt_beginner(params):
    return abmatt(params + ' -b brres_files/beginner_course.brres -d brres_files/test.brres -o')


def abmatt_water(params):
    return abmatt(params + ' -b brres_files/water_course.brres -d brres_files/test.brres -o')
