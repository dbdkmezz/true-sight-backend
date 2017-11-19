import pytest
import datetime
from django.test import TestCase

from project.apps.metadata.models import AdvantagesUpdate

from .factories import AdvantagesUpdateFactory


@pytest.mark.django_db
class TestModels(TestCase):
    def setUp(self):
        # don't know why I have to call this pytest should do this itself
        # must be something wrong with my config
        for u in AdvantagesUpdate.objects.all():
            u.delete()

    def testy(self):
        AdvantagesUpdateFactory(update_started=datetime.datetime(2017, 1, 1))
        AdvantagesUpdateFactory(update_started=datetime.datetime(2017, 1, 3))
        AdvantagesUpdateFactory(update_started=datetime.datetime(2017, 1, 2))

        assert AdvantagesUpdate.last_update_time().day == 3
