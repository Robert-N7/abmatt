import os

for file in os.listdir('.'):
    if 'test' in file and file.endswith('.py'):
        os.system(file)