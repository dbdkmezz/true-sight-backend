import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory
from apps.hero_abilities.factories import AbilityFactory

from .question_parser import QuestionParser


@pytest.mark.django_db
class TestQuestionParser(TestCase):
    def setUp(self):
        self.disruptor = HeroFactory(name='Disruptor')
        self.glimpse = AbilityFactory(name='Glimpse', hero=self.disruptor)

    def test_identify_abilities(self):
        parser = QuestionParser("What's the cooldown of Glimpse?", user_id=None)
        assert parser.abilities == [self.glimpse]

    def test_identify_abilities_name_substrings(self):
        AbilityFactory(name='Rage')
        chemical_rage = AbilityFactory(name='Chemical Rage')
        parser = QuestionParser("What's the cooldown of Chemical Rage?", user_id=None)
        assert parser.abilities == [chemical_rage]

    def test_identify_hero(self):
        parser = QuestionParser("What are Disruptor's abilities?", user_id=None)
        assert parser.heroes == [self.disruptor]

    def test_identify_heroes_in_order(self):
        storm_spirit = HeroFactory(name='Storm Spirit')
        parser = QuestionParser("Is Storm Spirit good against Disruptor?", user_id=None)
        assert parser.heroes == [storm_spirit, self.disruptor]

    def test_identify_heroes_in_order_with_two_letter_abbreviations(self):
        anti_mage = HeroFactory(name='Anti-Mage', aliases_data='AM')
        parser = QuestionParser("Is Disruptor good against AM?", user_id=None)
        assert parser.heroes == [self.disruptor, anti_mage]

    def test_identify_heroes_with_alias(self):
        wind_ranger = HeroFactory(name='Windranger', aliases_data='Wind Ranger')
        parser = QuestionParser("What are Wind Rangers abilities?", user_id=None)
        assert parser.heroes == [wind_ranger]

    def test_identify_hero_with_substring_alias(self):
        dark_willow = HeroFactory(name='Dark Willow', aliases_data='dark will')
        parser = QuestionParser("what's the dark Willows abilities", user_id=None)
        assert parser.heroes == [dark_willow]

    def test_identify_hero_with_common_substrings(self):
        lycan = HeroFactory(name='Lycan', aliases_data='lichen')
        HeroFactory(name='Lich')
        parser = QuestionParser("Lichen", user_id=None)
        assert parser.heroes == [lycan]

    def test_identify_two_letter_hero_abbrevations_if_whole_word(self):
        anti_mage = HeroFactory(name='Anti-Mage', aliases_data='AM')
        parser = QuestionParser('am', user_id=None)
        assert parser.heroes == [anti_mage]

    def test_dont_identify_two_letter_hero_abbrevations_if_not_whole_words(self):
        HeroFactory(name='Anti-Mage', aliases_data='AM')
        parser = QuestionParser('Pam', user_id=None)
        assert parser.heroes == []

    def test_yes(self):
        parser = QuestionParser("Yes.", user_id=None)
        assert parser.yes
