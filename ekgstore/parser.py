# -*- coding: utf-8 -*-
"""Defines parsing methods and processing routines."""
from __future__ import division
import ast
import contextlib
import hashlib
import json
import numpy as np
import os
import pandas as pd
import re

from codecs import open
from pyquery import PyQuery as pq

from . import inkscape
from .logger import logger


class Parser(object):
  """Base SVG parsing class.

  Parser class is the first step in EKG PDF parsing. It begins by preparing
  SVG of the PDF using Inkscape and strips away unnecessary elements from it.

  The methods here basically define few heuristics that have been seen to work
  for extracting the relevant information from the SVG tree.

  To understand the method, one needs to be familiar with SVG format. A quick
  cheatsheet follows:

      - SVG document is a collection of "elements" encoded in XML format.
      - The elements, represented by XML nodes contain relevant properties that
        contain information that instruct a SVG parser how to "draw" them. There
        are many SVG elements defined in its protocol. The relevant ones are:

          + ``g``: Group. This can contain any number of elements within it. Any
            property set to it can be inherited by all the "children" nodes.
          + ``text``: Defines a text node.
          + ``path``: Defines a "path" node.

      - Each SVG element can have properties that control their "look" much
        similar to what CSS does to elements in an HTML document.

          + ``d``: Specifies the coordinates on a "path" element.

      - Path encoding - Suppose you have a path with coordinates
          ``[(1, 1), (2, 10), (3, 15)]``. The encoding is in the following ways:

          + Absolute path: ``'M 1,1 2,10 3,15'``
          + Relative path: ``'m 1,1 1,9 1,5'``

  Args:
      file (str): Path to the PDF file.
      timeout (Optional[float]): Specify an optional timeout which is supplied
          to Inkscape.
  """
  def __init__(self, file, timeout=None, *arg, **kwa):
    self._pdf_file_path_ = os.path.abspath(file)
    self._timeout = timeout

  def _make_svg_(self):
    """Convert the pdf to svg file if necessary and initialize parser.

    To obtain the SVG, we find the md5 hash of the PDF file's path. This allows
    us to uniquely refer the files in a temporary location (``/tmp``) without
    any conflicts due to similar file names or very long paths.

    If the svg file already exist at ``/tmp`` (because it was previously
    converted) then we do not bother converting it yet again and simply proceed
    to parsing.

    This method uses the ``inkscape`` wrapper to convert the pdf files to svg.
    The svg file is processed by XML parsing utility called ``PyQuery``.
    """
    svg_hash = hashlib.md5(self._pdf_file_path_.encode()).hexdigest()
    svg_path = '/tmp/{0}.svg'.format(svg_hash)

    if not os.path.exists(svg_path):
      inkscape.convert(
          location=self._pdf_file_path_,
          destination=svg_path,
          timeout=self._timeout)

    with open(svg_path, 'r', encoding='utf-8') as fl:
      content = fl.read().encode(encoding='utf-8')
      self._svg = pq(content)
      self._svg.remove_namespaces()
      self._strip_elements_()

  def _strip_elements_(self):
    """Remove unnecessary path elements from SVG tree.

    Since the SVG contained many elements which we do not need (such as grids),
    we can remove those elements to make parsing convinient.
    """
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

  def export(self):
    """Parser subclasses can implement this method to generate the result."""
    raise NotImplemented

  @property
  def svg(self):
    """Convinience property to obtain the SVG instance."""
    if not hasattr(self, '_svg'):
      self._make_svg_()
    return self._svg

  @classmethod
  def process(cls, flname, *arg, **kwa):
    """Convinience method to process the file and obtain result."""
    obj = cls(flname, *arg, **kwa)
    return obj.export()


class Waveform(Parser):
  """Extract and Process the Waveforms, labels and Scaling factors.

  The waveforms in SVG tree are SVG-Path elements using the relative "path
  expression". This basically allows this parser to obtain each coordinate
  with respect to the previous one.

  Now, if we know the absolute coordinate of the first point, we can infer the
  rest by performing the relative movement.

  It was also discovered that the waveform path elements have their label text
  nodes as a sibling node. All this is coded in the ``get_waves`` method.
  """
  def _path_as_waveform_(self, path, offset=None):
    """Parse SVG path to coordinates.

    This method converts the "relative" path string to absolute coordinates.
    If the ``offse`t` parameter is supplied, we use that for the first
    coordinate, otherwise we assume them to be ``(0, 0)``.

    One problem here is, however, that we have many calibration markers on the
    pdf, corresponding to each ECG "strips". Hence, we require to figure out
    which strip corresponds to which waveform.

    This is solved by finding the baseline of each waveform by taking the mean
    of the absolute coordinates, and then finding the closest offset to that.

    Using that value for first coordinate allows us to get absolute values
    of waveform coordinates.

    Args:
        path (str): SVG Path String
        offset (Optional[list]): Coordinates of the offset values.

    Returns:
        Waveform in absolute coordinates.

    Raises:
        AssertionError: If ``path`` is not a relative SVG path expression.
    """
    # This parses the SVG path
    assert type(path) is str, 'Expected path to be a string.'
    assert path[0] is 'm', 'Expected path to be relative SVG.m expression.'
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
    """Infer x and y axis units from the calibration markers.

    This finds the length and height of the markers on the left. Since we know
    that the markers are supposed to be ``10 mm`` high and ``5 mm`` long, we
    can find the factor values by unitary method.
    """
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
    """Find the first coordinate of the calibration markers.

    Since we infer the absolute coordinates of the waveform path from preceeding
    coordinate, we require to find the absolute coordinate of the first one.

    We solve this by using the calibration markers as the absolute and use
    it as the "baseline" zero coordinate.
    """
    pattern = r'm (-?[\d\.]+,-?[\d\.]+)'
    with supress(AttributeError):
      markers = (unit_marker
          .map(lambda: re.match(pattern, pq(this).attr('d')).groups()[0]))
      return np.array(list(map(ast.literal_eval, markers)))

  def get_waves(self):
    """Find waveforms and markers in the SVG.

    This method utilises the SVG properties discussed above. We use the
    heuristic that the labels and paths are siblings. Also, the calibration
    markers do not have the labels.

    Since we have already stripped out all the path elements that are straight
    lines, the only ones left are waveforms and calibration markers.

    We proceed using above two facts by first anchoring to all the path nodes,
    then asserting if they have a text element as sibling. This leaves us with
    only the waveform elements with their labels.

    To obtain the calibration markers, we simply filter out the waveforms.

    Having the calibration markers, we use them to find the offset that will
    be useful to find absolute coordinate from waveform path and the scaling
    factors for ``x`` and ``y`` axes.

    Next, we use the ``_path_as_waveform_`` method with offsets to obtain the
    absolute waveforms, hence solving this problem.
    """
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
    """Perform the heuristics to obtain the waveform dataframes and factors."""
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
  """Convinience method to catch exceptions implicitly."""
  try:
    yield
  except exceptions:
    pass


class Metadata(Parser):
  def get_text_nodes(self):
    """Obtain the text nodes along with their coordinates.

    The text nodes are positioned via a transformation matrix. We parse this
    matrix here and obtain the ``(x, y)`` coordinates of the nodes from it.

    By scaling these coordinates by a factor of ``1/100`` we can "clump
    together" nodes that are closer, hence easing the heuristic filtering later.
    """
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
    """Use heuristics to infer text nodes to structured data.

    This uses the supplied heuristics of the positions of various text elements
    in the SVG tree to filter data and label them.

    The procedure is greedy -- we try to find as many elements that match our
    parameters as possible.

    We use the ``x``, ``y`` coordinates to approximate decision tree that
    groups the data after applying several normalization as can be seen in code.
    """
    text_nodes = self.get_text_nodes()
    meta = {}

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
    """Apply heuristics to obtain metadata from the PDF."""
    return self.infer_text()


def build_stack(file_name, *arg, **kwa):
  """File processing Routine.

  This routine processes the input file to extract the waveform, factors
  and the metadata.

  It ensures that a minimum amount of metadata is discovered before moving
  further. These metadata are scaling factors and ID.

  We use the Scale values in metadata with factors returned by ``Waveform`` to
  calculate the final scaling factors which is added as columns to the
  dataframes.
  """
  logger.debug('----> Extracting Waveforms')
  csv, units = Waveform.process(file_name, *arg, **kwa)
  logger.debug('----> Extracting Header Metadata')
  meta = Metadata.process(file_name, *arg, **kwa)

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

def process_stack(file_name, out_path, *arg, **kwa):
  """Process inputs and write the result to disk.

  Args:
      file_name (str): Path to the file.
      out_path (str): Where to write the result at.
      Additional arguments are passed on to ``build_stack``.
  """
  csv, meta = build_stack(file_name, *arg, **kwa)

  outfl = os.path.basename(file_name)[:-4]
  oid = meta['ID']

  csv.to_csv('{0}/{1}_{2}.csv'.format(out_path, oid, outfl), index=False)
  logger.debug('----> Writing Waveform to CSV')

  logger.debug('----> Writing Metadata to JSON')
  with open('{0}/{1}_{2}.json'.format(out_path, oid, outfl), 'w') as fl:
    json.dump(meta, fl, indent=2)


__all__ = ('Waveform', 'Metadata', 'process_stack')
