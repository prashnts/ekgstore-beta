import nose
import numpy as np

from ekgstore import _dir_
from ekgstore.parser import build_stack


def test_usage():
  csv, meta = build_stack(_dir_ + '/dat/test2_pass.pdf')

  assert meta['ID'] == '011489879'
  assert meta['Scale_x'] == '25mm/s'
  assert meta['Scale_y'] == '10mm/mV'

def test_incorrect():
  try:
    build_stack(_dir_ + '/dat/test4_fail.pdf')
  except Exception:
    assert True
  else:
    assert False, 'Expected AssertionError'

def test_integrity():
  csv, meta = build_stack(_dir_ + '/dat/test2_pass.pdf')

  np.testing.assert_allclose(
    csv['actual_X'][:5],
    [0.264, 0.268, 0.272, 0.276, 0.28])
  np.testing.assert_allclose(
    csv['actual_Y'][:5],
    [-0.264, -0.254, -0.244, -0.244, -0.244])
