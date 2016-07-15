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

import contextlib

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
        self._strip_elements_()

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


@contextlib.contextmanager
def supress(*exceptions):
  try:
    yield
  except exceptions:
    pass


class Metadata(Parser):
  def get_text_nodes(self):
    def node_transform(el):
      try:
        transform_mat = ast.literal_eval(el.attr('transform')[6:])
        x, y = list(transform_mat)[4:]
      except (ValueError, SyntaxError):
        x, y = 0, 0
      text_content = el.text()
      return [x // 100, y // 100, text_content]

    nodes_paired = list(map(node_transform, (self.svg
        .find('text')
        .items())))

    return pd.DataFrame(nodes_paired, columns=['x', 'y', 'text'])

  def infer_text(self):
    text_nodes = self.get_text_nodes()
    meta = {}

    # XXX: This section is pretty much a hack, and may not be robust.
    top_row = (text_nodes
        .query('y == 204')
        .sort_values('x')
        .text
        .values)

    with supress(IndexError):
      meta['Name'] = top_row[0]
      meta['ID'] = top_row[1].split(':')[1]
      meta['Date'] = top_row[2]

    with supress(IndexError):
      meta['Sex'] = (text_nodes
          .query('x == 4 and y == 194')
          .text
          .values[0])
    with supress(IndexError):
      meta['Ethnicity'] = (text_nodes
          .query('x == 19 and y == 194')
          .text
          .values[0])
    with supress(IndexError):
      meta['Weight'] = (text_nodes
          .query('x == 19 and y == 191')
          .text
          .values[0])
    with supress(IndexError):
      meta['Height'] = (text_nodes
          .query('x == 4 and y == 191')
          .text
          .values[0])

    meta['Remarks'] = '\n'.join((text_nodes
        .query('x == 119')
        .text
        .values[:-1]))

    eeg_report_keys = text_nodes.query('x == 54')
    for row in eeg_report_keys.values:
      y_coor = row[1]
      rvalues = (text_nodes
          .query('y == {0} and 50 < x < 110'.format(y_coor))
          .sort_values('x')
          .text
          .values)
      key = rvalues[0]
      value = ' '.join(rvalues[1:])
      meta[key] = value

    bottom_row = (text_nodes
        .query('y == 11')
        .sort_values('x')
        .text
        .values)

    with supress(IndexError):
      meta['Scale_x'] = bottom_row[0]
      meta['Scale_y'] = bottom_row[1]
      meta['Signal'] = bottom_row[2]

    split_and_strip = lambda x: [y.strip() for y in x.split(':')]
    meta.update(dict(map(split_and_strip, (text_nodes
        .query('y == 162')
        .sort_values('x')
        .text
        .values))))

    meta.update(dict(map(split_and_strip, (text_nodes
        .query('x == 4 and 100 < y < 190')
        .sort_values('y', ascending=False)
        .text
        .values))))

    meta.update(dict(map(split_and_strip, (text_nodes
        .query('x == 32')
        .sort_values('y', ascending=False)
        .text
        .values))))

    normalise_key = lambda x: re.sub(r'[^\w\d\s\-_\\]+', '', x)
    normal_meta = {normalise_key(k): v for k, v in meta.items()}
    return normal_meta

  def export(self):
    return self.infer_text()


__all__ = ('Waveform', 'Metadata')
