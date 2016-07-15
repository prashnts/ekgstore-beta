import os
import click
import glob
import datetime

from ekgstore import logger
from ekgstore.parser import process_stack


def process_pdf(file_name, output_dir, *arg, **kwa):
  try:
    logger.info('--> Begin: {0}'.format(file_name))
    process_stack(file_name, output_dir)
    logger.info('----> Done')
    return True
  except Exception as e:
    logger.error('----> Fail: ' + str(e))

@click.command()
@click.argument('in_dir', type=click.Path(exists=True))
@click.argument('out_dir', type=click.Path())
def ekg_routine(in_dir, out_dir):
  input_dir = os.path.abspath(in_dir)
  output_dir = os.path.abspath(out_dir)
  pdfs = glob.glob('{0}/*.pdf'.format(input_dir))

  logger.info('--> Discovered {0} PDF files'.format(len(pdfs)))

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
  begin = datetime.datetime.now()

  for pdf in pdfs:
    if process_pdf(pdf, output_dir):
      success += 1
    else:
      fail += 1

  end = datetime.datetime.now()
  elapsed = (end - begin).total_seconds()

  logger.info('----> Summary:')
  logger.info('--> Suceeded:    {0}\tfiles'.format(str(success)))
  logger.info('--> Errored:     {0}\tfiles'.format(str(fail)))
  logger.info('--> Total:       {0}\tfiles'.format(str(len(pdfs))))
  logger.info('--> Output dir:  {0}'.format(output_dir))
  logger.info('--> Elapsed:     {0} seconds'.format(str(elapsed)))
