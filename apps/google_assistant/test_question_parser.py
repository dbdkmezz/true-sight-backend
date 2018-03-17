import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory
from apps.hero_abilities.factories import AbilityFactory

from .question_parser import QuestionParser


@pytest.mark.django_db
class TestQuestionParser(TestCase):
    def setUp(self):
        self.glimpse = AbilityFactory(name='Glimpse')
        self.disruptor = HeroFactory(name='Disruptor')

    def test_identify_abilities(self):
        parser = QuestionParser("What's the cooldown of Glimpse?")
        assert parser.abilities == [self.glimpse]

    def test_identify_abilities_name_substrings(self):
        AbilityFactory(name='Rage')
        chemical_rage = AbilityFactory(name='Chemical Rage')
        parser = QuestionParser("What's the cooldown of Chemical Rage?")
        assert parser.abilities == [chemical_rage]

    def test_identify_hero(self):
        parser = QuestionParser("What are Disruptor's abilities?")
        assert parser.heroes == [self.disruptor]

    def test_identify_heroes_in_order(self):
        storm_spirit = HeroFactory(name='Storm Spirit')
        parser = QuestionParser("Is Storm Spirit good against Disruptor?")
        assert parser.heroes == [storm_spirit, self.disruptor]

    def test_identify_heroes_with_alias(self):
        wind_ranger = HeroFactory(name='Windranger', aliases_data='Wind Ranger')
        parser = QuestionParser("What are Wind Rangers abilities?")
        assert parser.heroes == [wind_ranger]

    def test_identify_hero_with_substring_alias(self):
        dark_willow = HeroFactory(name='Dark Willow', aliases_data='dark will')
        parser = QuestionParser("what's the dark Willows abilities")
        assert parser.heroes == [dark_willow]

    def test_yes(self):
        parser = QuestionParser("Yes.")
        assert parser.yes
