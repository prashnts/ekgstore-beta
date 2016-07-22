# -*- coding: utf-8 -*-
# EKGStore
from ekgstore.parser import Waveform, Metadata
from ekgstore.logger import logger

__all__ = ('Waveform', 'Metadata')

__version_info__ = (0, 3, 5)
__version__ = '.'.join(map(str, __version_info__))
