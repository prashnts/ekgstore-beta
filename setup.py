import re
import ast

from codecs import open
from os import path
from setuptools import setup


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), 'r', encoding='utf-8') as fl:
  long_description = fl.read()

with open(path.join(here, 'ekgstore', '__init__.py'), 'r') as fl:
  version_str = re.search(r'__version_info__ = (.*)', fl.read(), re.M).group(1)
  version = '.'.join(map(str, ast.literal_eval(version_str)))

setup(
  name='ekgstore',
  description='Parses and extracts metadata and waveforms from EKG files.',
  long_description=long_description,
  version=version,
  author='Prashant Sinha',
  author_email='prashant@ducic.ac.in',
  packages=['ekgstore'],
  install_requires=[
    'pyquery',
    'numpy',
    'click',
    'pandas',
    'tqdm',
  ],
  tests_require=[
    'nose',
  ],
  test_suite='nose.collector',
  entry_points='''
    [console_scripts]
    ekgstore=ekgstore.console:ekg_routine
  ''',
  include_package_data=True,
)
