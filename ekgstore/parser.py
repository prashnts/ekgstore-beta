"""EKG PDF Parsing Routine
Convert PDF to SVG using inkscape, extract waveform from the SVG and
normalise the waveform.

# Usage
See ekgstore.Parser.

# Cavetes
For easier XML parsing, we strip away the namespace declaration from
SVG, hence should need be to export, namespace must be appended.
"""
from __future__ import division
import os
import re
import ast
import subprocess
import pandas as pd
import numpy as np

from pyquery import PyQuery as pq


class Parser(object):
  """Extract Waveforms with Annotations

  # Args
  - pdf_fl (str): Path to the PDF file. Relative paths are fine.

  # Usage
  Make an object with path to valid PDF:
  >>> obj = Parser('./dat/sample1.pdf')

  ## Get labeled waveform and units tuple:
  >>> waveform, units = obj.get_waves()

  # Exceptions
  - RuntimeError: Raised if the SVG couldn't be generated.
  """
  def __init__(self, pdf_fl):
    self._fl_loc = os.path.abspath(pdf_fl)

  def __mk_svg__(self):
    """Convert PDF to SVG"""
    svg_fl_name = '{0}.svg'.format(self._fl_loc)
    try:
      if not os.path.exists(svg_fl_name):
        subprocess.check_output([
          'inkscape',
          '--file={0}'.format(self._fl_loc),
          '--export-plain-svg={0}'.format(svg_fl_name),
          '--without-gui',
        ])
    except EnvironmentError:
      raise RuntimeError('`inkscape` binary is required.')
    except subprocess.CalledProcessError:
      raise RuntimeError('Cannot convert the provided file to SVG.')
    else:
      with open(svg_fl_name, 'r') as fl:
        self._svg = pq(fl.read().encode())
        self._svg.remove_namespaces()

  @property
  def svg(self):
    """Memoized access to SVG XML tree"""
    if not hasattr(self, '_svg'):
      self.__mk_svg__()
    return self._svg

  @classmethod
  def process(cls, flname):
    obj = cls(flname)
    return obj.export()


class Waveform(Parser):
  def _strip_elements_(self):
    """Remove unnecessary path elements"""
    # Remove svg definitions from the tree
    (self.svg
        .find('defs')
        .remove())

    # Remove paths which are composed of straight lines
    path_pattern = r'm -?[\d\.]+,-?[\d\.]+ (-?[\d\.]+,0 ?|0,-?[\d\.]+ ?)+z?$'
    (self.svg
        .find('path')
        .filter(lambda: re.match(path_pattern, pq(this).attr('d')) is not None)
        .remove())
    # Remove all groups without any children nodes.
    (self.svg
        .find('g:empty')
        .remove())

  def _path_as_waveform_(self, path, offset=None):
    """Parse SVG path to coordinates"""
    # This parses the SVG path
    assert path[0] is 'm'
    path = path[2:]
    steps = [list(map(float, _.split(','))) for _ in path.split(' ')]
    steps_pair = list(map(list, zip(*steps)))

    for i in range(2):
      if offset is not None:
        delta = steps_pair[i][0] - offset[:,i]
        steps_pair[i][0] = delta[np.abs(delta).argsort()[0]]
      else:
        steps_pair[i][0] = 0

    return [np.cumsum(x) for x in steps_pair]

  def _get_units_(self, unit_marker):
    """Infer x and y axis units from the marker"""
    # assuming the wave on left is for marking units
    arr_range = lambda x: x.max() - x.min()
    x_steps, y_steps = self._path_as_waveform_(unit_marker)

    x_sz = len(x_steps)
    x_unit = 1 / (x_sz * 25)
    # Two blocks
    y_sz = arr_range(y_steps)
    y_unit = 10 / y_sz
    return x_unit, y_unit

  def _get_offsets_(self, unit_marker):
    pattern = r'm (-?[\d\.]+,-?[\d\.]+)'
    markers = (unit_marker
        .map(lambda: re.match(pattern, pq(this).attr('d')).groups()[0]))

    return np.array(list(map(ast.literal_eval, markers)))

  def get_waves(self):
    """Find waveforms in the SVG"""
    self._strip_elements_()
    # we want to look at waves that also have the annotations
    text_anchor_els = (self.svg
        .find('path')
        .parent()
        .next('g')
        .find('text'))
    # Wave elements that we're interested in were in the previous element.
    waveform_els = (text_anchor_els
        .parent()
        .prev()
        .find('path'))
    if not text_anchor_els:
      # Fallback
      text_anchor_els = (self.svg
          .find('path')
          .next('text'))
      waveform_els = (text_anchor_els.prev())

    node_repr = lambda x: pq(x).__repr__()
    waveform_repr = waveform_els.map(lambda: node_repr(this))
    wave_paths = waveform_els.map(lambda: pq(this).attr('d'))
    unit_markers = (self.svg
        .find('path')
        .filter(lambda: node_repr(this) not in waveform_repr))
    unit_marker = unit_markers.attr('d')

    offset = self._get_offsets_(unit_markers)
    labels = text_anchor_els.map(lambda: pq(this).text())
    waveform = [self._path_as_waveform_(x, offset) for x in wave_paths]
    return list(zip(labels, waveform)), self._get_units_(unit_marker)

  def export(self):
    waves, units = self.get_waves()
    x_unit, y_unit = units
    rows = []
    for label, waveform in waves:
      for x, y in zip(*waveform):
        x_scaled = x * x_unit
        y_scaled = y * y_unit
        rows.append([label, x, y, x_scaled, y_scaled])

    columns = ('lead', 'absoluteX', 'absoluteY', 'actual_X', 'actual_Y')
    df = pd.DataFrame(rows, columns=columns)
    return df



__all__ = ('Parser', 'Waveform')
