"""EKG PDF Parsing Routine
Convert PDF to SVG using inkscape, extract waveform from the SVG and
normalise the waveform.

# Usage
See ekgstore.Parser.

# Cavetes
For easier XML parsing, we strip away the namespace declaration from
SVG, hence should need be to export, namespace must be appended.
"""
import os
import subprocess
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
      subprocess.check_output([
        'inkscape',
        '--file={0}'.format(self._fl_loc),
        '--export-plain-svg={0}'.format(svg_fl_name),
        '--without-gui',
      ])
    except FileNotFoundError:
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

  def _strip_elements_(self):
    """Remove unnecessary path elements"""
    stroke = 'stroke-width:15'
    # Remove all the paths that aren't having `stroke` same as above.
    (self.svg
        .find('path:not(path[style*="{0}"])'.format(stroke))
        .remove())
    # Remove all groups without any children nodes.
    (self.svg
        .find('g:empty')
        .remove())

  def _path_as_waveform_(self, path):
    """Parse SVG path to coordinates"""
    # This parses the SVG path
    assert path[0] is 'm'
    path = path[2:]
    steps = [list(map(float, _.split(','))) for _ in path.split(' ')]
    steps_pair = [[0.0] + list(_)[1:] for _ in zip(*steps)]
    return [np.cumsum(_) for _ in steps_pair]

  def _get_units_(self, unit_marker):
    """Infer x and y axis units from the marker"""
    # assuming the wave on left is for marking units
    arr_range = lambda x: x.max() - x.min()
    x_steps, y_steps = self._path_as_waveform_(unit_marker)

    x_unit = arr_range(x_steps) / len(x_steps)
    x_unit = len(x_steps)
    # Two blocks
    y_unit = arr_range(y_steps) / 2
    return x_unit, y_unit

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
    unit_marker = (self.svg
        .find('path')
        .filter(lambda: node_repr(this) not in waveform_repr)
        .attr('d'))
    labels = text_anchor_els.map(lambda: pq(this).text())
    waveform = [self._path_as_waveform_(x)[1] for x in wave_paths]
    return dict(zip(labels, waveform)), self._get_units_(unit_marker)


__all__ = ('Parser',)
