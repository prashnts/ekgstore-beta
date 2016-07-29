"""Wrapper around Inkscape commandline app."""
import os
import re
import sys

if os.name == 'posix' and sys.version_info[0] < 3:
  import subprocess32 as subprocess
else:
  import subprocess


def get_args(**kwa):
  """Build arguments that are supplied to Inkscape commandline app.

  Notes:
  - Only keyword arguments are supported.
  - To pass flags, supply them with `=True`.
  - Only "truthy" values are appended.
  - To supply arguments with hyphen, use "camelCase". Examples:
    + version => --version
    + withoutGui => --without-gui
    + withoutGUI => --without-g-u-i (Attention!)
    + exportPlainSvg => --export-plain-svg
  """
  args = ['inkscape']

  for key, value in kwa.items():
    key = re.sub('([A-Z]+)', r'-\1', key).lower()

    if value and type(value) is not bool:
      args.append('--{0}={1}'.format(key, value))
    elif value:
      args.append('--{0}'.format(key))

  assert len(args) > 1, 'No arguments supplied.'
  return args


def passthru(timeout=None, **kwa):
  """Spawn Inkscape subprocess.

  Args:
  - timeout (float, optional): If supplied, the subprocess is killed after
    the timeout period.
  - Additional arguments are passed on to `get_args`.

  Raises:
  - RuntimeError: For any exception with subprocess.
  """
  try:
    return subprocess.check_output(get_args(**kwa), timeout=timeout)
  except EnvironmentError:
    raise RuntimeError('`inkscape` binary is required.')
  except subprocess.CalledProcessError:
    raise RuntimeError('Operation failed.')
  except subprocess.TimeoutExpired:
    raise RuntimeError('Operation timed out.')


def version():
  """Find the version of inkscape binary"""
  out = passthru(version=True)
  vinfo = out.decode()
  assert vinfo.startswith('Inkscape'), 'Unknown Inkscape version.'
  return vinfo[9:14]


def convert(location, destination, timeout=None):
  """Convert file at `location` to `destination` with optional `timeout`."""
  return passthru(
      file=location,
      exportPlainSvg=destination,
      withoutGui=True,
      timeout=timeout)

