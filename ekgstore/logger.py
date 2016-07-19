import logging
import os
import datetime

from logging import StreamHandler, FileHandler


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

dtformat = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
file_log_name = '{0}/EKG_Extraction_{1}.log'.format(os.getcwd(), dtformat)
file_handle = FileHandler(file_log_name)
file_handle.setFormatter(file_log_format)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handle)
logger.addHandler(file_handle)
