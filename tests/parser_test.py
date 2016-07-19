import nose
import numpy as np

from ekgstore.parser import Waveform


class TestWaveform:
  test_path = 'm 100,100 10,10 10,-5 10,0 10,8'
  test_offset = np.array([
    [50, 90],
    [50, 290],
    [50, 390],
  ])

  def __init__(self):
    self.p = Waveform('.')

  def test_path_as_waveform_(self):
    pairs = self.p._path_as_waveform_(self.test_path, self.test_offset)

    assert all(np.equal(pairs[0], [50, 60, 70, 80, 90]))
    assert all(np.equal(pairs[1], [10, 20, 15, 15, 23]))

  def test_closest_move(self):
    test_path = 'm 100,250 10,10 10,-5 10,0 10,8'
    pairs = self.p._path_as_waveform_(test_path, self.test_offset)

    assert all(np.equal(pairs[1], [-40, -30, -35, -35, -27]))

  def test_closest_jump(self):
    test_path = 'm 100,250 10,10 10,-200 10,0 10,8'
    pairs = self.p._path_as_waveform_(test_path, self.test_offset)

    assert all(np.equal(pairs[1], [160, 170, -30, -30, -22]))

