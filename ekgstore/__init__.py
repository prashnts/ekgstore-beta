# -*- coding: utf-8 -*-
# EKGStore
import os

from .parser import Waveform, Metadata
from .logger import logger

__all__ = ('Waveform', 'Metadata')

__version_info__ = (0, 5, 1)
__version__ = '.'.join(map(str, __version_info__))

_dir_ = os.path.dirname(__file__)
