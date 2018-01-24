import random
import string
import factory

from apps.utils.factories import random_string, random_bool
from apps.hero_advantages.tests.factories import HeroFactory

from .models import Ability


class AbilityFactorty(factory.DjangoModelFactory):
    class Meta:
        model = Ability

    hero = factory.SubFactory(HeroFactory)
    name = factory.LazyAttribute(lambda t: random_string(
        characters="{} -".format(string.ascii_letters)))
    cooldown = factory.LazyAttribute(lambda t: random_string())
    hotkey = factory.LazyAttribute(lambda t: random.choice(['q', 'w', 'e', 'r']))
    is_ultimate = factory.LazyAttribute(lambda t: random_bool())
