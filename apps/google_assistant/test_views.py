import pytest

from django.test import TestCase
from django.http import HttpResponse
from libs.google_actions.tests.mocks import MockRequest
from libs.google_actions.tests.utils import Utils as GoogleTestUtils

from apps.hero_abilities.factories import AbilityFactory
from apps.hero_advantages.factories import HeroFactory

from .views import index


@pytest.mark.django_db
class TestViews(TestCase):
    def test_hello_if_not_json(self):
        result = index(MockRequest(body='NOT JSON'))
        self.assertIsInstance(result, HttpResponse)
        self.assertIn("Hello", str(result.content))

    def test_basics_end_to_end(self):
        AbilityFactory(
            hero=HeroFactory(name='Disruptor'),
            name='Static Storm',
            is_ultimate=True,
        )
        response = make_request_and_return_text("what is Disruptor's ultimate")
        assert "Static Storm" in response


def make_request_and_return_text(text=None, user_id=None, conversation_token=None):
    response = index(
        MockRequest(text=text, user_id=user_id, conversation_token=conversation_token))
    return GoogleTestUtils.get_text_from_google_response(response)
