import random
import string
import factory

from apps.utils.factories import random_string, random_bool

from .models import Hero, Advantage


class HeroFactory(factory.DjangoModelFactory):
    class Meta:
        model = Hero

    name = factory.LazyAttribute(lambda t: random_string(
        characters="{} -".format(string.ascii_letters)))
    is_carry = factory.LazyAttribute(lambda t: random_bool())
    is_support = factory.LazyAttribute(lambda t: random_bool())
    is_off_lane = factory.LazyAttribute(lambda t: random_bool())
    is_jungler = factory.LazyAttribute(lambda t: random_bool())
    is_mid = factory.LazyAttribute(lambda t: random_bool())
    is_roaming = factory.LazyAttribute(lambda t: random_bool())


class AdvantageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Advantage

    hero = factory.SubFactory(HeroFactory)
    enemy = factory.SubFactory(HeroFactory)
    advantage = factory.LazyAttribute(lambda t: random.unoform(-10, 10))
