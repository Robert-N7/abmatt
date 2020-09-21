import os
import sys

from tests.integration.lib import bcolors

err_count = 0
for file in os.listdir('.'):
    if 'test' in file and file.endswith('.py'):
        err_count += os.system('"' + sys.executable + ' ' + file + '"')
if err_count:
    print(f'{bcolors.FAIL}{err_count} tests failed.{bcolors.ENDC}')