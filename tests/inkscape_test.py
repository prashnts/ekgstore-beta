import nose

from ekgstore.inkscape import get_args, passthru


def test_args_one():
  args = get_args(file='/test', exportPlainSvg='/test')

  assert args[0] == 'inkscape'
  assert args[1] == '--export-plain-svg=/test'
  assert args[2] == '--file=/test'


def test_args_two():
  args = get_args(version=True)

  assert args[1] == '--version'


def test_args_assertion():
  try:
    get_args()
  except AssertionError:
    pass
  else:
    assert False, 'Must raise AssertionError.'


def test_timeouts():
  try:
    passthru(timeout=1e-3, version=True)
  except RuntimeError:
    pass
  else:
    assert False, 'Timeout did not happen.'
