# -*- coding: utf-8 -*-
# EKGStore
import os

from ekgstore.parser import Waveform, Metadata
from ekgstore.logger import logger

__all__ = ('Waveform', 'Metadata')

__version_info__ = (0, 4, 2)
__version__ = '.'.join(map(str, __version_info__))

_dir_ = os.path.dirname(__file__)
