import os

err_count = 0
for file in os.listdir('.'):
    if 'test' in file and file.endswith('.py'):
        err_count += os.system(file)
if err_count:
    print('{} tests failed.'.format(err_count))