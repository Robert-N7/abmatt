#!/usr/bin/env python3
import os

import setuptools
from setuptools import setup

# reading long description from file
with open('README.md') as file:
    long_description = file.read()


REQUIREMENTS = ['fuzzywuzzy', 'python-Levenshtein', 'numpy', 'pillow', 'colorama', 'PyQt5', 'lxml']

# some more details
CLASSIFIERS = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent"
 ]

data_dir = 'etc/abmatt'
data_files = []
for file in os.listdir(data_dir):
    path = os.path.join(data_dir, file)
    if not os.path.isdir(path):
        data_files.append(path)

# calling the setup function
setup(name='abmatt',
      version='0.9.5',
      entry_points={
          'console_scripts': [
              'abmatt = abmatt.__main__:main'
          ],
          'gui_scripts': [
              'abmatt-gui = abmatt.gui.main_window:main'
          ]
      },
      description='Brres file material editor',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/Robert-N7/abmatt',
      author='Robert Nelson',
      author_email='robert7.nelson@gmail.com',
      license='GPLv3',
      packages=setuptools.find_packages(),
      data_files=[(data_dir, data_files)],
      classifiers=CLASSIFIERS,
      install_requires=REQUIREMENTS,
      keywords='Mario Kart Wii Brres Material Model'
      )
