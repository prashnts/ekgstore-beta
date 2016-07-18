import os
import click
import glob
import datetime

from ekgstore import logger, file_log_name
from ekgstore.parser import process_stack


def process_pdf(file_name, output_dir, *arg, **kwa):
  try:
    logger.info('--> Begin: {0}'.format(file_name))
    process_stack(file_name, output_dir)
    logger.info('----> Done')
    return True
  except Exception as e:
    logger.error('----> Fail {0}: '.format(file_name) + str(e))

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
  begin = datetime.datetime.now()

  files_processed = 0;
  for pdf in pdfs:
    files_processed += 1
    if process_pdf(pdf, output_dir):
      success += 1
    else:
      fail += 1
    if (files_processed % 2 == 0):
      print ('---> {0}/{1} files processed.'.format(files_processed, total_files_to_process))
      logger.info('---> {0}/{1} files processed.'.format(files_processed, total_files_to_process))

  end = datetime.datetime.now()
  elapsed = (end - begin).total_seconds()

  # Append ERROR logs at the end of log file
  logger.info('########################## Errors started ###########################')
  os.system("cat " + file_log_name + " | grep \"ERROR\" >> " + file_log_name)
  logger.info('########################## Errors ended ###########################')

  logger.info('########################## Summary started ###########################')
  logger.info('----> Summary:')
  logger.info('--> Suceeded:    {0}\tfiles'.format(str(success)))
  logger.info('--> Errored:     {0}\tfiles'.format(str(fail)))
  logger.info('--> Total:       {0}\tfiles'.format(str(len(pdfs))))
  logger.info('--> Output dir:  {0}'.format(output_dir))
  logger.info('--> Elapsed:     {0} seconds'.format(str(elapsed)))
  #logger.info('########################## Summary ended ###########################')

  try:
    with open('EKG_RUN_SUMMARY.txt', 'a') as f:
      f.write('\n\n----> Summary:\n')
      f.write('--> Log file name: {0}\t'.format(str(file_log_name)) + '\n')
      f.write('--> Suceeded:    {0}\tfiles'.format(str(success)) + "\n")
      f.write('--> Errored:     {0}\tfiles'.format(str(fail)) + "\n")
      f.write('--> Total:       {0}\tfiles'.format(str(len(pdfs))) + "\n")
      f.write('--> Output dir:  {0}'.format(output_dir) + "\n")
      f.write('--> Elapsed:     {0} seconds'.format(str(elapsed)) + "\n")
      f.close()
  except Exception as e:
    logger.error("Error in appending summary in EKG_RUN_SUMMARY.txt")
    logger.error(e)
