import os
from .base import *  # noqa


LOGGING['handlers']['file'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    'filename': os.path.join(os.sep, 'var', 'log', 'www', 'true-sight.log'),
}