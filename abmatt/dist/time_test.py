import time
import os
import sys

path = '__main__'
if not os.path.exists(path):
    path += '.exe'
    if not os.path.exists(path):
        print('Failed to find main!')
        sys.exit(1)

start_time = time.time()
os.system(path)
print('Ran for {}'.format(time.time() - start_time))