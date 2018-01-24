import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory
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
class TestParserAndResponder(TestCase):
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
        assert response == "The cooldown of Glimpse is 60/46/32/18 seconds"

    def test_ability_hotkey_response(self):
        responder = QuestionParser("What is Disruptor's W?").get_responder()
        response = responder.generate_response()
        assert response == "Disruptor's W is Glimpse"

    def test_hero_ultimate_response(self):
        responder = QuestionParser("What is Disruptor's ultimate?").get_responder()
        response = responder.generate_response()
        assert (
            response == "Disruptor's ultimate is Static Storm, it's cooldown is 90/80/70 seconds")

    def test_ability_list_response(self):
        responder = QuestionParser("What are Disruptor's abilities?").get_responder()
        response = responder.generate_response()
        assert (
            response == "Disruptor's abilities are Thunder Strike, Glimpse, and Static Storm")
