import random
import factory
import datetime

from ..models import AdvantagesUpdate


def random_datetime(
    earliest=datetime.datetime(2001, 1, 1),
    latest=datetime.datetime.today(),
):
    range = (latest - earliest).total_seconds()
    seconds = random.randint(0, int(range))
    return earliest + datetime.timedelta(0, seconds)


class AdvantagesUpdateFactory(factory.DjangoModelFactory):
    class Meta:
        model = AdvantagesUpdate

    update_started = factory.LazyAttribute(lambda t: random_datetime())
    update_finished = factory.LazyAttribute(lambda t: random_datetime())
