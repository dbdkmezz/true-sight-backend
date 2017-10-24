import os

from django import setup


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    setup()
