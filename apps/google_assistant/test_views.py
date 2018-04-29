import pytest

from django.test import TestCase
from django.http import HttpResponse
from libs.google_actions.tests.mocks import MockRequest
from libs.google_actions.tests.utils import Utils as GoogleTestUtils

from apps.hero_abilities.factories import AbilityFactory
from apps.hero_advantages.factories import HeroFactory, AdvantageFactory

from .views import index


@pytest.mark.django_db
class TestViews(TestCase):
    def test_hello_if_not_json(self):
        result = index(MockRequest(body='NOT JSON'))
        self.assertIsInstance(result, HttpResponse)
        self.assertIn("Hello", str(result.content))

    def test_response_if_not_understand(self):
        response = make_request_and_return_text("I love pizza")
        assert "Sorry" in response
        assert "I heard you say:" in response

    def test_basics_end_to_end(self):
        AbilityFactory(
            hero=HeroFactory(name='Disruptor'),
            name='Static Storm',
            is_ultimate=True,
        )
        response = make_request_and_return_text("what is Disruptor's ultimate")
        assert "Static Storm" in response

    def test_counters_end_to_end(self):
        storm_spirit = HeroFactory(name='Storm Spirit')
        queen_of_pain = HeroFactory(name='Queen of Pain')
        AdvantageFactory(hero=storm_spirit, enemy=queen_of_pain, advantage=1.75)
        response = make_request_and_return_text("what heroes are good against Queen of Pain")
        assert "Storm Spirit" in response

    def test_talk_to_ends_conversation(self):
        response = index(MockRequest(text="talk to ultimate quiz"))
        assert GoogleTestUtils.google_response_is_tell(response)
        response_text = GoogleTestUtils.get_text_from_google_response(response)
        assert 'True Sight' in response_text
        assert 'Goodbye' in response_text

    def test_talk_to_true_sight_plays_welcome(self):
        response = make_request_and_return_text("talk to true sight")
        assert "Gem of True Sight" in response

    def test_health_check_ends_conversation(self):
        response = index(MockRequest(health_check=True))
        assert GoogleTestUtils.google_response_is_tell(response)


def make_request_and_return_text(text=None, user_id=None, conversation_token=None):
    response = index(
        MockRequest(text=text, user_id=user_id, conversation_token=conversation_token))
    return GoogleTestUtils.get_text_from_google_response(response)
