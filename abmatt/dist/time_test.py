import subprocess
import time
import os
import sys


def get_path(prefix):
    if os.path.exists(prefix):
        if os.path.isdir(prefix):
            return get_path(os.path.join(prefix, prefix))
        else:
            return prefix
    elif not '.exe' in prefix:
        prefix += '.exe'
        return get_path(prefix)


def time_test(command):
    start_time = time.time()
    params = command.split(' ')
    result = subprocess.call(params)
    return time.time() - start_time


def main(argv):
    if not argv:
        test_count = 1
    else:
        test_count = int(argv.pop(0))
    path = get_path('main')
    params = ' -b ../../brres_files/beginner_course.brres -d ../../brres_files/test.brres -o'
    if not path:
        print('Failed to find abmatt!')
        sys.exit(1)
    command = path + params
    results = []
    for x in range(test_count):
        results.append(time_test(command))
    print('Ran {} tests. Average run time {}'.format(test_count, sum(results) / test_count))
    print('Minimum time {}'.format(min(results)))
    print('Maximum time {}'.format(max(results)))


if __name__ == '__main__':
    main(sys.argv[1:])