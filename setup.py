# -*- coding: utf-8 -*-
import ast
import os
import re
import sys

from codecs import open
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as fl:
  long_description = fl.read()

with open(os.path.join(here, 'ekgstore', '__init__.py'), 'r') as fl:
  version_str = re.search(r'__version_info__ = (.*)', fl.read(), re.M).group(1)
  version = '.'.join(map(str, ast.literal_eval(version_str)))

requires = [
  'click',
  'glob2',
  'numpy',
  'pandas',
  'pyquery',
  'tqdm',
]

if sys.version_info[0] < 3:
  requires.append('subprocess32')

setup(
  name='ekgstore',
  description='Parses and extracts metadata and waveforms from EKG files.',
  long_description=long_description,
  version=version,
  author='Prashant Sinha',
  author_email='prashant@ducic.ac.in',
  packages=['ekgstore'],
  install_requires=requires,
  tests_require=[
    'nose',
  ],
  test_suite='nose.collector',
  entry_points='''
    [console_scripts]
    ekgstore=ekgstore.console:ekg_routine
  ''',
  include_package_data=True,
  package_data=dict(ekgstore=['dat/*.pdf']),
)
