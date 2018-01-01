import os
from .base import *


LOGGING['handlers']['file'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    'filename': os.path.join(os.sep, 'var', 'log', 'www', 'true-sight.log'),
}

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'truesight',
    'USER': get_secret('DB_USER'),
    'PASSWORD': get_secret('DB_PASSWORD'),
    'HOST': 'localhost',
    'PORT': '',
}
