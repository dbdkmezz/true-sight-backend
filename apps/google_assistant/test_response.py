import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory, AdvantageFactory
from apps.hero_abilities.factories import AbilityFactory

from .response import ResponseGenerator, QuestionParser
from .exceptions import DoNotUnderstandQuestion


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

    def test_identify_heroes(self):
        parser = QuestionParser("What are Disruptor's abilities?")
        assert parser.heroes == [self.disruptor]

    def test_identify_heroes_with_alias(self):
        wind_ranger = HeroFactory(name='Windranger', aliases_data='Wind Ranger')
        parser = QuestionParser("What are Wind Rangers abilities?")
        assert parser.heroes == [wind_ranger]


@pytest.mark.django_db
class TestAbiltyParserAndResponders(TestCase):
    def setUp(self):
        disruptor = HeroFactory(name='Disruptor')
        AbilityFactory(
            hero=disruptor,
            name='Thunder Strike',
            hotkey='Q',
            is_ultimate=False,
        )
        AbilityFactory(
            hero=disruptor,
            name='Glimpse',
            cooldown='60/46/32/18',
            description=(
                'Teleports the target hero back to where it was 4 seconds ago. Instantly kills '
                'illusions.'),
            hotkey='W',
            is_ultimate=False,
        )
        AbilityFactory(
            hero=disruptor,
            name='Static Storm',
            cooldown='90/80/70',
            hotkey='R',
            is_ultimate=True,
        )

    def test_raises_does_not_understand(self):
        with self.assertRaises(DoNotUnderstandQuestion):
            ResponseGenerator.respond("What is a pizza?")

    def test_cooldown_response(self):
        response = ResponseGenerator.respond("What's the cooldown of Glimpse?")
        assert response == "The cooldown of Glimpse is 60, 46, 32, 18 seconds"

    def test_cooldown_two_words(self):
        response = ResponseGenerator.respond("What's the cool down of Glimpse?")
        assert response == "The cooldown of Glimpse is 60, 46, 32, 18 seconds"

    def test_when_no_cooldown(self):
        AbilityFactory(
            hero=HeroFactory(name='Pangolier'),
            name='Swashbuckle',
            cooldown='',
        )
        response = ResponseGenerator.respond("What's the cool down of Swashbuckle?")
        assert response == "Swashbuckle is a passive ability, with no cooldown"

    def test_ability_hotkey_response(self):
        response = ResponseGenerator.respond("What is Disruptor's W?")
        assert response == (
            "Disruptor's W is Glimpse. Teleports the target hero back to where it was 4 seconds "
            "ago. Instantly kills illusions.")

    def test_hero_ultimate_response(self):
        response = ResponseGenerator.respond("What is Disruptor's ultimate?")
        assert (
            response == "Disruptor's ultimate is Static Storm, it's cooldown is 90, 80, 70 seconds"
        )

    def test_ability_list_response(self):
        response = ResponseGenerator.respond("What are Disruptor's abilities?")
        assert (
            response == "Disruptor's abilities are Thunder Strike, Glimpse, and Static Storm")

    def test_ability_list_response_excludes_talent_abilities(self):
        phantom_lancer = HeroFactory(name='Phantom Lancer')
        AbilityFactory(
            hero=phantom_lancer,
            name='Critical Strike',
            is_from_talent=True,
        )
        AbilityFactory(
            hero=phantom_lancer,
            name='Juxtapose',
        )

        response = ResponseGenerator.respond("What are Phantom Lancer's abilities?")
        assert 'Juxtapose' in response
        assert 'Critical Strike' not in response


@pytest.mark.django_db
class TestAdvantageParserAndResponders(TestCase):
    def setUp(self):
        storm_spirit = HeroFactory(name='Storm Spirit', is_mid=True)
        queen_of_pain = HeroFactory(name='Queen of Pain', is_mid=True)
        shadow_fiend = HeroFactory(name='Shadow Fiend', is_mid=True)
        razor = HeroFactory(name='Razor', is_mid=True)
        zeus = HeroFactory(name='Zeus', is_mid=True)
        sniper = HeroFactory(name='Sniper', is_mid=True)
        disruptor = HeroFactory(name='Disruptor', is_mid=False, is_support=True)

        AdvantageFactory(hero=queen_of_pain, enemy=storm_spirit, advantage=2.14)
        AdvantageFactory(hero=sniper, enemy=storm_spirit, advantage=-3.11)
        AdvantageFactory(hero=shadow_fiend, enemy=storm_spirit, advantage=0.55)
        AdvantageFactory(hero=razor, enemy=storm_spirit, advantage=0.66)
        AdvantageFactory(hero=zeus, enemy=storm_spirit, advantage=-4.50)
        AdvantageFactory(hero=disruptor, enemy=storm_spirit, advantage=1.75)

    def test_general_advantage(self):
        response = ResponseGenerator.respond("Which heroes are good against Storm Spirit?")
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Disruptor, Razor, and Shadow Fiend are also good"
        )

    def test_mid_advantage(self):
        response = ResponseGenerator.respond("Which mid heroes are good against Storm Spirit?")
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Razor and Shadow Fiend are also good"
        )
