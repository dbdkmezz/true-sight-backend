import os
from .base import *  # noqa


SETTINGS_URI_PATH = 'admin'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s %(asctime)s %(name)s] %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'true-sight.log'),
            'formatter': 'verbose',
        },
        'good_response_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'good-response.log'),
        },
        'failed_response_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'failed-response.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'good_response': {
            'handlers': ['good_response_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'failed_response': {
            'handlers': ['failed_response_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
