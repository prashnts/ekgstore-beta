import os
import click
import glob
import datetime

from tqdm import tqdm
from ekgstore import logger
from ekgstore.logger import error_log_name, summary_log_name, file_log_name
from ekgstore.parser import process_stack


def process_pdf(file_name, output_dir, *arg, **kwa):
  try:
    logger.debug('--> Begin: {0}'.format(file_name))
    process_stack(file_name, output_dir)
    logger.debug('----> Done')
    return True
  except Exception as e:
    logger.error('----> Fail: {0}'.format(file_name))
    logger.exception('------> Stack Trace:')

@click.command()
@click.argument('in_dir', type=click.Path(exists=True))
@click.argument('out_dir', type=click.Path())
def ekg_routine(in_dir, out_dir):
  """EKG Store

  Parses and extracts metadata and waveforms from the EKG PDF data files.
  """
  input_dir = os.path.abspath(in_dir)
  output_dir = os.path.abspath(out_dir)
  pdfs = glob.glob('{0}/*.pdf'.format(input_dir))
  total_files_to_process = len(pdfs)
  begin = datetime.datetime.now()

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
    if process_pdf(pdf, output_dir):
      success += 1
    else:
      fail += 1

  end = datetime.datetime.now()
  elapsed = (end - begin).total_seconds()

  logger.info('--> Summary:')
  logger.info('----> Suceeded    {0}\tfiles'.format(str(success)))
  logger.info('----> Errored     {0}\tfiles'.format(str(fail)))
  logger.info('----> Total       {0}\tfiles'.format(str(len(pdfs))))
  logger.info('----> Output dir  {0}'.format(output_dir))
  logger.info('----> Elapsed     {0} seconds'.format(str(elapsed)))
  logger.info('--> Log Files:')
  logger.info('----> Summary     {0}'.format(summary_log_name))
  logger.info('----> Errors      {0}'.format(error_log_name))
  logger.info('----> Complete    {0}\n\n'.format(file_log_name))
