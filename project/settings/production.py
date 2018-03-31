import os
from .base import *


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s %(asctime)s %(name)s] %(message)s',
        },
        'time':  {
            'format': '[%(asctime)s] %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'true-sight.log'),
            'formatter': 'verbose',
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'error.log'),
            'formatter': 'verbose',
        },
        'good_response_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'good-response.log'),
            'formatter': 'time',
        },
        'failed_response_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.sep, 'var', 'log', 'www', 'failed-response.log'),
            'formatter': 'time',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {
            'handlers': ['error'],
            'level': 'ERROR',
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


DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'truesight',
    'USER': get_secret('DB_USER'),
    'PASSWORD': get_secret('DB_PASSWORD'),
    'HOST': 'localhost',
    'PORT': '',
}
