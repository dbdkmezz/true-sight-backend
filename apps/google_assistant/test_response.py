import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory, AdvantageFactory
from apps.hero_abilities.factories import AbilityFactorty

from .response import QuestionParser
from .exceptions import DoNotUnderstandQuestion


@pytest.mark.django_db
class TestQuestionParser(TestCase):
    def setUp(self):
        self.glimpse = AbilityFactorty(name='Glimpse')

    def test_identify_abilities(self):
        parser = QuestionParser("What's the cooldown of Glimpse?")
        assert parser.abilities == [self.glimpse]

    def test_raises_does_not_understand(self):
        parser = QuestionParser("What is a pizza?")
        with self.assertRaises(DoNotUnderstandQuestion):
            parser.get_responder()


@pytest.mark.django_db
class TestAbiltyParserAndResponders(TestCase):
    def setUp(self):
        disruptor = HeroFactory(name='Disruptor')
        AbilityFactorty(
            hero=disruptor,
            name='Thunder Strike',
            hotkey='Q',
            is_ultimate=False,
        )
        AbilityFactorty(
            hero=disruptor,
            name='Glimpse',
            cooldown='60/46/32/18',
            hotkey='W',
            is_ultimate=False,
        )
        AbilityFactorty(
            hero=disruptor,
            name='Static Storm',
            cooldown='90/80/70',
            hotkey='R',
            is_ultimate=True,
        )

    def test_cooldown_response(self):
        responder = QuestionParser("What's the cooldown of Glimpse?").get_responder()
        response = responder.generate_response()
        assert response == "The cooldown of Glimpse is 60, 46, 32, 18 seconds"

    def test_cooldown_two_words(self):
        responder = QuestionParser("What's the cool down of Glimpse?").get_responder()
        response = responder.generate_response()
        assert response == "The cooldown of Glimpse is 60, 46, 32, 18 seconds"

    def test_ability_hotkey_response(self):
        responder = QuestionParser("What is Disruptor's W?").get_responder()
        response = responder.generate_response()
        assert response == "Disruptor's W is Glimpse"

    def test_hero_ultimate_response(self):
        responder = QuestionParser("What is Disruptor's ultimate?").get_responder()
        response = responder.generate_response()
        assert (
            response == "Disruptor's ultimate is Static Storm, it's cooldown is 90, 80, 70 seconds")

    def test_ability_list_response(self):
        responder = QuestionParser("What are Disruptor's abilities?").get_responder()
        response = responder.generate_response()
        assert (
            response == "Disruptor's abilities are Thunder Strike, Glimpse, and Static Storm")


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
        responder = QuestionParser("Which heroes are good against Storm Spirit?").get_responder()
        response = responder.generate_response()
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Disruptor, Razor, and Shadow Fiend are also good"
        )

    def test_mid_advantage(self):
        responder = QuestionParser(
            "Which mid heroes are good against Storm Spirit?").get_responder()
        response = responder.generate_response()
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Razor and Shadow Fiend are also good"
        )
