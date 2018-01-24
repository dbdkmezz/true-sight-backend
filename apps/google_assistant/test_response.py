import pytest

from django.test import TestCase

from apps.hero_advantages.tests.factories import HeroFactory
from apps.hero_abilities.factories import AbilityFactorty

from .response import QuestionParser


@pytest.mark.django_db
class TestQuestionParser(TestCase):
    def setUp(self):
        self.glimpse = AbilityFactorty(name='Glimpse')

    def test_identify_abilities(self):
        parser = QuestionParser("What's the cooldown of Glimpse?")
        assert parser.abilities == [self.glimpse]


@pytest.mark.django_db
class TestParserAndResponder(TestCase):
    def setUp(self):
        disruptor = HeroFactory(name='Disruptor')
        AbilityFactorty(hero=disruptor, name='Glimpse', cooldown='60/46/32/18')
        AbilityFactorty(hero=disruptor, name='Thunder Strike')

    def test_cooldown_response(self):
        responder = QuestionParser("What's the cooldown of Glimpse?").get_responder()
        response = responder.generate_response()
        assert response == "The cooldown of Glimpse is 60/46/32/18 seconds"

    def test_ability_list_response(self):
        responder = QuestionParser("What are Disruptor's abilities?").get_responder()
        response = responder.generate_response()
        assert (
            response == "Disruptor's abilities are Glimpse, and Thunder Strike"
            or response == "Disruptor's abilities are Thunder Strike, and Glimpse")
