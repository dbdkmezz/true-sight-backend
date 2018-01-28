import os
from .base import *  # noqa


SETTINGS_URI_PATH = 'admin'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'true-sight.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
