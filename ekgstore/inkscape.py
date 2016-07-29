import os
import sys
import re

if os.name == 'posix' and sys.version_info[0] < 3:
  import subprocess32 as subprocess
else:
  import subprocess


def get_args(**kwa):
  args = ['inkscape']

  for key, value in kwa.items():
    key = re.sub('([A-Z]+)', r'-\1', key).lower()

    if value:
      args.append('--{0}={1}'.format(key, value))
    elif value:
      args.append('--{0}'.format(key))

  assert len(args) > 1, 'No arguments supplied.'
  return args


def passthru(timeout=None, **kwa):
  try:
    return subprocess.check_output(get_args(**kwa), timeout=timeout)
  except EnvironmentError:
    raise RuntimeError('`inkscape` binary is required.')
  except subprocess.CalledProcessError:
    raise RuntimeError('Operation failed.')
  except subprocess.TimeoutExpired:
    raise RuntimeError('Operation timed out.')


def version():
  out = passthru(version=True)
  vinfo = out.decode()
  assert vinfo.startswith('Inkscape'), 'Unknown Inkscape version.'
  return vinfo[9:14]


def convert(location, destination, timeout=None):
  return passthru(
      file=location,
      exportPlainSvg=destination,
      withoutGui=True,
      timeout=timeout)

