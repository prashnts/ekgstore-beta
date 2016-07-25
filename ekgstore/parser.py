# -*- coding: utf-8 -*-
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
import json
import hashlib
import pandas as pd
import numpy as np

import contextlib

from pyquery import PyQuery as pq
from codecs import open

from ekgstore import inkscape
from ekgstore.logger import logger


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
    svg_hash = hashlib.md5(self._fl_loc.encode()).hexdigest()
    svg_file = '/tmp/{0}.svg'.format(svg_hash)

    if not os.path.exists(svg_file):
      inkscape.convert(location=self._fl_loc, destination=svg_file)

    with open(svg_file, 'r', encoding='utf-8') as fl:
      self._svg = pq(fl.read().encode(encoding='utf-8'))
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
    assert type(path) is str, 'Expected "path" to be a string.'
    assert path[0] is 'm', 'Expected "path" to be relative SVG.m expression.'
    path = path[2:]
    steps = [list(map(float, _.split(','))) for _ in path.split(' ')]

    # [[xi..], [yi..]]
    steps_pair = list(map(list, zip(*steps)))

    for i in range(2):
      if offset is not None:
        axis_approx = np.cumsum(steps_pair[i]).mean()
        delta_initial = steps_pair[i][0] - offset[:,i]
        delta_axial = axis_approx - offset[:,i]
        closest_axis_index = np.abs(delta_axial).argsort()[0]
        steps_pair[i][0] = delta_initial[closest_axis_index]
      else:
        steps_pair[i][0] = 0

    return [np.cumsum(x) for x in steps_pair]

  def _get_units_(self, unit_marker):
    """Infer x and y axis units from the marker"""
    # assuming the wave on left is for marking units
    arr_range = lambda x: x.max() - x.min()
    step_size = lambda x: (x[1:] - x[:-1]).mean()
    x_steps, y_steps = self._path_as_waveform_(unit_marker)
    x_signal = x_steps[y_steps > 0]

    x_step = step_size(x_steps)
    # Compensate for the "transition on the begining and end"
    x_sz = 5.0 / (arr_range(x_signal) + x_step)
    # Two blocks
    y_sz = 10.0 / (arr_range(y_steps))
    return x_sz, y_sz

  def _get_offsets_(self, unit_marker):
    pattern = r'm (-?[\d\.]+,-?[\d\.]+)'
    with supress(AttributeError):
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
    rows = []
    for label, waveform in waves:
      for x, y in zip(*waveform):
        rows.append([label, x, y])

    columns = ('lead', 'absoluteX', 'absoluteY')
    df = pd.DataFrame(rows, columns=columns)
    return df, units


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

    with supress(TypeError):
      meta['Remarks'] = '\n'.join((text_nodes
          .query('x == 119')
          .text
          .values[:-1]))

    with supress(IndexError):
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

    with supress(ValueError):
      meta.update(dict(map(split_and_strip, (text_nodes
          .query('y == 162')
          .sort_values('x')
          .text
          .values))))

    with supress(ValueError):
      meta.update(dict(map(split_and_strip, (text_nodes
          .query('x == 4 and 100 < y < 190')
          .sort_values('y', ascending=False)
          .text
          .values))))

    with supress(ValueError):
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


def build_stack(file_name):
  logger.debug('----> Extracting Waveforms')
  csv, units = Waveform.process(file_name)
  logger.debug('----> Extracting Header Metadata')
  meta = Metadata.process(file_name)

  logger.debug('----> Verifying Data Integrity')
  assert 'Scale_x' in meta, "Can't find `Scale_x` in Metadata."
  assert 'Scale_y' in meta, "Can't find `Scale_y` in Metadata."
  assert 'mm/s' in meta['Scale_x'], "Expected unit `mm/s` in `Scale_x`."
  assert 'mm/mV' in meta['Scale_y'], "Expected unit `mm/mV` in `Scale_y`."
  assert 'ID' in meta, "Can't find `ID` in Metadata."

  logger.debug('----> Applying axial scaling')
  factor_x, factor_y = [int(re.match(r'(\d+)', meta[f]).group(0))
      for f in ['Scale_x', 'Scale_y']]
  unit_x, unit_y = units
  csv['actual_X'] = csv['absoluteX'] * (1 / factor_x) * unit_x
  csv['actual_Y'] = csv['absoluteY'] * (1 / factor_y) * unit_y

  return csv, meta

def process_stack(file_name, out_path):
  csv, meta = build_stack(file_name)

  outfl = os.path.basename(file_name)[:-4]
  oid = meta['ID']

  csv.to_csv('{0}/{1}_{2}.csv'.format(out_path, oid, outfl), index=False)
  logger.debug('----> Writing Waveform to CSV')

  logger.debug('----> Writing Metadata to JSON')
  with open('{0}/{1}_{2}.json'.format(out_path, oid, outfl), 'w') as fl:
    json.dump(meta, fl, indent=2)


__all__ = ('Waveform', 'Metadata', 'process_stack')
