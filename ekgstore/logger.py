import logging
import os
import datetime

from logging import StreamHandler, FileHandler


class InfoLevelFilter(logging.Filter):
  def filter(self, record):
    return record.levelno == logging.INFO


file_log_format = logging.Formatter(
  "%(asctime)s - %(levelname)-8s%(module)s.%(funcName)s:%(lineno)d %(message)s",
  "%Y-%m-%d %H:%M:%S"
)
console_log_format = logging.Formatter(
  "%(asctime)s %(message)s",
  "%H:%M:%S"
)

console_handle = StreamHandler()
console_handle.setFormatter(console_log_format)
console_handle.addFilter(InfoLevelFilter())
console_handle.setLevel(logging.INFO)

dtformat = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
file_log_name = '{0}/EKG_Extraction_{1}.log'.format(os.getcwd(), dtformat)
file_handle = FileHandler(file_log_name)
file_handle.setFormatter(file_log_format)
file_handle.setLevel(logging.DEBUG)

summary_log_name = '{0}/EKG_Run_Summary_{1}.log'.format(os.getcwd(), dtformat)
summary_log_handle = FileHandler(summary_log_name)
summary_log_handle.setFormatter(file_log_format)
summary_log_handle.setLevel(logging.INFO)

logger = logging.getLogger('ekgstore')
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handle)
logger.addHandler(file_handle)
logger.addHandler(summary_log_handle)
