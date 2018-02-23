import pytest
from unittest.mock import patch

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory, AdvantageFactory
from apps.hero_abilities.factories import AbilityFactory
from apps.hero_abilities.models import SpellImmunity

from .response import ResponseGenerator
from .exceptions import DoNotUnderstandQuestion, Goodbye


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
            name='Kinetic Field',
            spell_immunity=SpellImmunity.DOES_NOT_PIERCE,
            spell_immunity_detail=(
                "The Barrier's modifier persists if it was placed before spell immunity."),
            hotkey='E',
            is_ultimate=False,
        )
        AbilityFactory(
            hero=disruptor,
            name='Static Storm',
            cooldown='90/80/70',
            hotkey='R',
            is_ultimate=True,
        )

    @patch('apps.google_assistant.response.failed_response_logger')
    def test_raises_does_not_understand_and_logs(self, failed_response_logger):
        with self.assertRaises(DoNotUnderstandQuestion):
            ResponseGenerator.respond("What is a pizza?")
        assert failed_response_logger.warning.call_count == 1
        assert failed_response_logger.warning.call_args[0][0].startswith(
            'Unable to respond to question.')

    @patch('apps.google_assistant.response_text.ResponderUse')
    def test_logs_responder_use(self, ResponderUse):
        ResponseGenerator.respond("What's does Disruptor's Glimpse ablity do?")
        ResponderUse.log_use.assert_called_with('AbilityDescriptionResponse')

    def test_fallback_ability_response(self):
        response, _ = ResponseGenerator.respond("What's does Disruptor's Glimpse ablity do?")
        assert response == (
            "Disruptor's ability Glimpse. Teleports the target hero back to where it was 4 "
            "seconds ago. Instantly kills illusions. its cooldown is 60, 46, 32, 18 seconds.")

    def test_cooldown_response(self):
        response, conversation_token = ResponseGenerator.respond("What's the cooldown of Glimpse?")
        assert response == (
            "The cooldown of Glimpse is 60, 46, 32, 18 seconds. Would you like to know the "
            "cooldown of another ability?")
        assert conversation_token['context-class'] == 'AbilityCooldownContext'

    def test_cooldown_two_words(self):
        response, _ = ResponseGenerator.respond("What's the cool down of Glimpse?")
        assert response == (
            "The cooldown of Glimpse is 60, 46, 32, 18 seconds. Would you like to know the "
            "cooldown of another ability?")

    def test_ability_hotkey_response(self):
        response, _ = ResponseGenerator.respond("What is Disruptor's W?")
        assert response == (
            "Disruptor's W is Glimpse. Teleports the target hero back to where it was 4 seconds "
            "ago. Instantly kills illusions.")

    def test_hero_ultimate_response(self):
        response, _ = ResponseGenerator.respond("What is Disruptor's ultimate?")
        assert (
            response == "Disruptor's ultimate is Static Storm, its cooldown is 90, 80, 70 seconds."
        )

    def test_ability_list_response(self):
        response, _ = ResponseGenerator.respond("What are Disruptor's abilities?")
        assert response == (
            "Disruptor's abilities are Thunder Strike, Glimpse, Kinetic Field, and Static Storm.")

    def test_spell_immunity_response(self):
        response, _ = ResponseGenerator.respond(
            "Does spell immunity protect against Kinetic Field?")
        assert response == (
            "Kinetic Field does not pierce spell immunity. The Barrier's modifier persists if it "
            "was placed before spell immunity.")

    @pytest.mark.skip("Bug not fixed yet")
    def test_abilities_with_the_same_name(self):
        AbilityFactory(
            hero=HeroFactory(name='Lion'),
            name='Hex',
            cooldown='30/24/18/12',
        )
        AbilityFactory(
            hero=HeroFactory(name='Shadow Shaman'),
            name='Hex',
            cooldown='13',
        )
        response, _ = ResponseGenerator.respond("What's the cooldown of Hex?")
        assert response == (
            "Both Lion and Shadow Shaman have the Hex ability. Lion's cooldown is 13, Shadow "
            "Shaman's is 30, 24, 18, 12 seconds.")

    def test_context_increments_useage_count(self):
        response, conversation_token = ResponseGenerator.respond(
            "What's the cooldown of Thunder Strike?")
        assert response.endswith('Would you like to know the cooldown of another ability?')
        assert conversation_token['useage_count'] == 0
        response, conversation_token = ResponseGenerator.respond(
            "What's the cooldown of Thunder Strike?", conversation_token)
        assert response.endswith('Any other abilities?')
        assert conversation_token['useage_count'] == 1


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
        AdvantageFactory(hero=storm_spirit, enemy=queen_of_pain, advantage=1.75)

    def test_single_enemy_advantage(self):
        response, _ = ResponseGenerator.respond("Which heroes are good against Storm Spirit?")
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Disruptor, Razor, and Shadow Fiend are also good."
        )

    def test_mid_advantage(self):
        response, _ = ResponseGenerator.respond("Which mid heroes are good against Storm Spirit?")
        assert response == (
            "Queen of Pain is very strong against Storm Spirit. "
            "Razor and Shadow Fiend are also good."
        )

    def test_two_hero_advantage(self):
        response, _ = ResponseGenerator.respond("Is Disruptor good against Storm Spirit?")
        assert response == (
            "Disruptor is not bad against Storm Spirit. Disruptor's advantage is 1.75.")


@pytest.mark.django_db
class TestFollowUpRespones(TestCase):
    def test_yes(self):
        AbilityFactory(name='Glimpse', cooldown='60/46/32/18')
        AbilityFactory(name='Static Storm', cooldown='90/80/70')

        _, token = ResponseGenerator.respond('What is the cooldown of Glimpse?')
        response, token = ResponseGenerator.respond('Yes.', token)
        assert response == 'Which ability?'
        response, token = ResponseGenerator.respond('Static Storm', token)
        assert '90' in response
        assert 'Any other' in response

    def test_no(self):
        AbilityFactory(name='Glimpse', cooldown='60/46/32/18')

        _, token = ResponseGenerator.respond('What is the cooldown of Glimpse?')
        with self.assertRaises(Goodbye):
            ResponseGenerator.respond('Nope.', token)
