"""Defines logging files and parameters."""
import datetime
import logging
import os

from logging import StreamHandler, FileHandler


class InfoLevelFilter(logging.Filter):
  """Filter class to only log `INFO` level."""
  def filter(self, record):
    return record.levelno == logging.INFO

class ErrorLevelFilter(logging.Filter):
  """Filter class to only log `ERROR` level."""
  def filter(self, record):
    return record.levelno == logging.ERROR

file_log_format = logging.Formatter(
  "%(asctime)s - %(levelname)-8s%(module)s.%(funcName)s:%(lineno)d %(message)s",
  "%Y-%m-%d %H:%M:%S"
)
console_log_format = logging.Formatter("%(message)s")
error_log_format = logging.Formatter(
  '"%(asctime)s",%(levelname)s,"%(module)s.%(funcName)s:%(lineno)d",%(message)s\r',
  "%Y-%m-%d %H:%M:%S"
)

console_handle = StreamHandler()
console_handle.setFormatter(console_log_format)
console_handle.addFilter(InfoLevelFilter())
console_handle.setLevel(logging.INFO)

dtformat = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
file_log_name = '{0}/EKG_Extraction_{1}.log'.format(os.getcwd(), dtformat)
summary_log_name = '{0}/EKG_Run_Summary.txt'.format(os.getcwd())
error_log_name = '{0}/EKG_Extraction_Errors_{1}.csv'.format(os.getcwd(), dtformat)


def attach_file_loggers(logger):
  """Initialize log files to `logger`."""
  file_handle = FileHandler(file_log_name)
  file_handle.setFormatter(file_log_format)
  file_handle.setLevel(logging.DEBUG)

  summary_log_handle = FileHandler(summary_log_name)
  summary_log_handle.setFormatter(console_log_format)
  summary_log_handle.setLevel(logging.INFO)
  summary_log_handle.addFilter(InfoLevelFilter())

  error_log_handle = FileHandler(error_log_name)
  error_log_handle.setFormatter(error_log_format)
  error_log_handle.setLevel(logging.DEBUG)
  error_log_handle.addFilter(ErrorLevelFilter())

  logger.addHandler(file_handle)
  logger.addHandler(summary_log_handle)
  logger.addHandler(error_log_handle)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handle)
