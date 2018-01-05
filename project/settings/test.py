from .base import *  # noqa


DEBUG = True


# Put log file in parent folder so looponfail doesn't run tests endlessly
LOGGING['handlers']['file'] = {
    'level': 'DEBUG',
    'class': 'logging.FileHandler',
    'filename': BASE_DIR.ancestor(2).child('debug.log'),
}
