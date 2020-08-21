import time
import os
import sys

path = 'abmatt'
params = ' -b ../../brres_files/beginner_course.brres -d ../../brres_files/test.brres'
if not os.path.exists(path):
    path += '.exe'
    if not os.path.exists(path):
        print('Failed to find abmatt!')
        sys.exit(1)

start_time = time.time()
os.system(path + params)
print('Ran for {}'.format(time.time() - start_time))