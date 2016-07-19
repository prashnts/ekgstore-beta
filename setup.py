from setuptools import setup

setup(
  name='ekgstore',
  version='0.2.4',
  packages=['ekgstore'],
  install_requires=[
    'pyquery',
    'numpy',
    'click',
    'pandas',
    'tqdm',
  ],
  entry_points='''
    [console_scripts]
    ekgstore=ekgstore.console:ekg_routine
  ''',
)
