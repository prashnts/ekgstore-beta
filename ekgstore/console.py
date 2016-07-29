# -*- coding: utf-8 -*-
"""Defines the console app commands."""
import click
import datetime
import glob2 as glob
import os
import sys
import time

from tqdm import tqdm

from . import logger, __version__, _dir_, inkscape
from .logger import (error_log_name, summary_log_name, file_log_name,
    attach_file_loggers)
from .parser import process_stack


def process_pdf(file_name, output_dir, *arg, **kwa):
  """Parse and write the output to specified directory.

  Args:
  - file_name (str): File to be processed.
  - output_dir (str): Location where to write the output.

  Notes:
  - Additional arguments are passed on to `stack_processing`.
  - This method supresses any exception raised by `stack_processing`.
  """
  try:
    logger.debug('--> Begin: {0}'.format(file_name))
    process_stack(file_name, output_dir, *arg, **kwa)
    logger.debug('----> Done')
    return True
  except Exception as e:
    exc = sys.exc_info()
    logger.error('"{0}","{1}"'.format(file_name, exc[1]))
    logger.debug('------> Stack Trace:', exc_info=exc)


def warmup():
  """Verify integrity of Inkscape application and discover runtime parameters.

  Since the time taken to convert a pdf to svg is dictated by Inkscape, this
  method supplies a typical example file and notices the time taken to perform
  the conversion. We use this `time` later in timeout heuristics where we abort
  the svg conversion of a pdf file if it takes 3x longer than the time we
  discovered earlier. This gives us an acceptable safeguard against various
  many pdf files that this tool isn't supposed to act upon, but is accidentally
  supplied.
  """
  logger.info('==> Warming-up')
  logger.info('----> Inkscape Version: {0}'.format(inkscape.version()))
  logger.info('----> Calibrating runtime...')
  tick = time.time()
  inkscape.convert('{0}/dat/test2_pass.pdf'.format(_dir_), '/dev/null')
  elapsed = (time.time() - tick) * 3
  logger.info('----> Conversion timeout (3x): {0}'.format(str(elapsed)))
  return elapsed


@click.command()
@click.option('-i', '--input',
    multiple=True,
    default=['**/*.pdf'],
    metavar='<path/pattern>',
    help='Input files or patterns (check examples).')
@click.option('-o', '--output',
    default='./output',
    metavar='<path>',
    help='Output directory.')
@click.option('-x', '--no-logging',
    is_flag=True,
    help='Do not write any log files.')
def ekg_routine(input, output, no_logging):
  """Parse and extract metadata and waveforms from ECG files.

  As default behaviour, this tool will find all the files in current directory
  and all subdirectories and write output to directory called "output".

  More advanced behaviour is supported by supplying '-i' (or '--input') and
  '-o' (or '--output') options. Check out the examples below for usage.

  \b
  Examples:
  1. (default) Process all files in current and all children directories. Write
     all output in "output" directory:
      $ ekgstore
  \b
  2. Process files in directories "foo" and "bar" only:
      $ ekgstore -i foo -i bar

  \b
  3. Process a single file:
      $ ekgstore -i path/to/file.pdf

  \b
  4. Process all files like "anna_1.pdf", "anna_2.pdf" etc. in any directory:
      $ ekgstore -i '**/anna_*.pdf'

  \b
  5. Specify output directory:
      $ ekgstore -o path/to/directory

  \b
  Notes:
  - Multiple input files are acceptable. The arguments can either be directory
    names or patterns.
  - Supply input files via "-i" or "--input" followed by your input.
  - To supply multiple files, simply chain them.
  - '/*.pdf' is appended to the input patterns if they do not end with '.pdf'.
  - Glob patterns MUST be wrapped within single quotes (').

  """
  if not no_logging:
    attach_file_loggers(logger)
  pdfs = []
  for pattern in input:
    if not pattern.endswith('.pdf'):
      pattern += '/*.pdf'
    for path in glob.glob(pattern):
      if path.endswith('.pdf'):
        pdfs.append(os.path.abspath(path))
  output_dir = os.path.abspath(output)

  total_files_to_process = len(pdfs)
  begin = datetime.datetime.now()

  logger.info('==> EKGStore v{0}'.format(__version__))

  timeout = warmup()

  logger.info('--> Began at {0}'.format(begin.strftime('%b/%d/%Y %I:%M:%S %p')))
  logger.info('--> Discovered {0} PDF files'.format(total_files_to_process))

  if os.path.exists(output_dir):
    if not os.path.isdir(output_dir):
      logger.error('--> "{0}" is not a directory.'.format(out_dir))
      raise click.Abort
  else:
    try:
      os.makedirs(output_dir)
    except OSError:
      logger.error('--> Path "{0}" is not accessible.'.format(out_dir))
      raise click.Abort

  success, fail = 0, 0

  for pdf in tqdm(pdfs, desc='--> Processed', unit='files'):
    if process_pdf(pdf, output_dir, timeout=timeout):
      success += 1
    else:
      fail += 1

  end = datetime.datetime.now()
  elapsed = (end - begin).total_seconds()

  logger.info('==> Summary:')
  logger.info('----> Suceeded    {0}\tfiles'.format(str(success)))
  logger.info('----> Errored     {0}\tfiles'.format(str(fail)))
  logger.info('----> Total       {0}\tfiles'.format(str(len(pdfs))))
  logger.info('----> Output dir  {0}'.format(output_dir))
  logger.info('----> Elapsed     {0} seconds'.format(str(elapsed)))

  if not no_logging:
    logger.info('==> Log Files:')
    logger.info('----> Summary     {0}'.format(summary_log_name))
    logger.info('----> Errors      {0}'.format(error_log_name))
    logger.info('----> Complete    {0}\n\n'.format(file_log_name))
  else:
    logger.info('==> Log Files not written.')
