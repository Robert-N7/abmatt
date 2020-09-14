import setuptools
from setuptools import setup

# reading long description from file
with open('README.md') as file:
    long_description = file.read()


# specify requirements of your package here
REQUIREMENTS = ['fuzzywuzzy', 'python-Levenshtein', 'numpy']

# some more details
CLASSIFIERS = [
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.8",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent"
 ]

# calling the setup function
setup(name='abmatt',
      version='0.7.0',
      entry_points={
          'console_scripts': [
              'abmatt = abmatt.__main__:main',
              'convert-dae = abmatt.converters.convert_dae:main'
              'convert-obj = abmatt.converters.convert_obj:main'
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
      package_data={'abmatt': ['presets.txt', 'config.conf']},
      classifiers=CLASSIFIERS,
      install_requires=REQUIREMENTS,
      keywords='Mario Kart Wii Brres Material Model'
      )
