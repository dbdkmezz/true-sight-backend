import pytest
from unittest.mock import patch

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory, AdvantageFactory
from apps.hero_abilities.factories import AbilityFactory
from apps.hero_abilities.models import SpellImmunity, DamageType

from .response import ResponseGenerator, Context, FreshContext
from .exceptions import DoNotUnderstandQuestion, Goodbye


class TestWelcomeAndIntroduction(TestCase):
    def test_welcome_message(self):
        response, token = ResponseGenerator.respond(None)
        assert "True Sight" in response
        assert token is not None

        response, token = ResponseGenerator.respond("")
        assert "True Sight" in response
        assert token is not None

    def test_what_can_you_do(self):
        response, token = ResponseGenerator.respond("What can you do?")
        assert "counters" in response
        assert "abilities" in response
        assert token is not None

    def test_can_ask_questions_after_welcome(self):
        AbilityFactory(
            name='Static Storm',
            cooldown='90/80/70',
        )
        _, token = ResponseGenerator.respond(None)
        response, _ = ResponseGenerator.respond("What is the cooldown of static storm?", token)
        assert "90" in response


@pytest.mark.django_db
class TestAbiltyParserAndResponders(TestCase):
    def setUp(self):
        disruptor = HeroFactory(name='Disruptor')
        AbilityFactory(
            hero=disruptor,
            name='Thunder Strike',
            hotkey='Q',
            is_ultimate=False,
            damage_type=DamageType.MAGICAL,
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
        AbilityFactory(
            hero=HeroFactory(name='Sniper'),
            name='Assassinate',
            is_ultimate=True,
            damage_type=DamageType.MAGICAL,
            aghanims_damage_type=DamageType.PHYSICAL,
        )

    @patch('apps.google_assistant.response.failed_response_logger')
    def test_raises_does_not_understand_and_logs(self, failed_response_logger):
        with self.assertRaises(DoNotUnderstandQuestion):
            ResponseGenerator.respond("What is a pizza?")
        assert failed_response_logger.warning.call_count == 1

    @patch('apps.google_assistant.response_text.ResponderUse')
    def test_logs_responder_use(self, ResponderUse):
        ResponseGenerator.respond("What's does Disruptor's Glimpse ablity do?", user_id='USERID')
        ResponderUse.log_use.assert_called_with('AbilityDescriptionResponse', 'USERID')

    def test_fallback_ability_response(self):
        response, _ = ResponseGenerator.respond("What's does Disruptor's Glimpse ablity do?")
        assert (
            "Disruptor's ability Glimpse. Teleports the target hero back to where it was 4 "
            "seconds ago. Instantly kills illusions. Its cooldown is 60, 46, 32, 18 seconds."
            in response)

    def test_cooldown_response(self):
        response, conversation_token = ResponseGenerator.respond("What's the cooldown of Glimpse?")
        assert "The cooldown of Glimpse is 60, 46, 32, 18 seconds." in response
        assert conversation_token['context-class'] == 'SingleAbilityContext'

    def test_cooldown_two_words(self):
        response, _ = ResponseGenerator.respond("What's the cool down of Glimpse?")
        assert "The cooldown of Glimpse is" in response

    def test_ability_hotkey_response(self):
        response, _ = ResponseGenerator.respond("What is Disruptor's W?")
        assert (
            "Disruptor's W is Glimpse. Teleports the target hero back to where it was 4 seconds "
            "ago. Instantly kills illusions."
            in response)

    def test_hero_ultimate_response(self):
        response, _ = ResponseGenerator.respond("What is Disruptor's ultimate?")
        assert (
            "Disruptor's ultimate is Static Storm, its cooldown is 90, 80, 70 seconds."
            in response)

    def test_hero_ultimate_response_multiple_ultimates(self):
        dark_willow = HeroFactory(name='Dark Willow')
        AbilityFactory(
            hero=dark_willow,
            name='Bedlam',
            cooldown='40,30,20',
            is_ultimate=True,
        )
        AbilityFactory(
            hero=dark_willow,
            name='Terrorize',
            cooldown='40,30,20',
            is_ultimate=True,
        )
        response, context = ResponseGenerator.respond("What is Dark Willow's ultimate?")
        assert response == (
            "<speak>Dark Willow has multiple ultimates: Bedlam and Terrorize.</speak>")
        assert not context

    def test_ability_list_response(self):
        response, _ = ResponseGenerator.respond("What are Disruptor's abilities?")
        assert (
            "Disruptor's abilities are Thunder Strike, Glimpse, Kinetic Field, and Static Storm. "
            in response)

    def test_spell_immunity_response(self):
        response, _ = ResponseGenerator.respond(
            "Does spell immunity protect against Kinetic Field?")
        assert response == (
            "<speak>Kinetic Field does not pierce spell immunity. "
            "The Barrier's modifier persists if it was placed before spell immunity. "
            "Anything else you'd like to know about it?</speak>")

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
        assert conversation_token['useage-count'] == 1
        response, conversation_token = ResponseGenerator.respond(
            "What's it's cooldown?", conversation_token)
        assert conversation_token['useage-count'] == 2

    def test_damage_type(self):
        response, _ = ResponseGenerator.respond("What's the damage type of Thunder Strike?")
        assert 'magical' in response

    def test_aghs_damage_type(self):
        response, _ = ResponseGenerator.respond("What's the damage type of Assassinate?")
        assert 'magical' in response
        assert "with Aghanim's Scepter it does physical damage" in response


@pytest.mark.django_db
class TestAdvantageParserAndResponders(TestCase):
    def setUp(self):
        self.setUpAdvantages()

    @staticmethod
    def setUpAdvantages():
        storm_spirit = HeroFactory(name='Storm Spirit', is_mid=True)
        queen_of_pain = HeroFactory(name='Queen of Pain', is_mid=True, is_support=False)
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
        assert response.startswith(
            "<speak>Queen of Pain is very strong against Storm Spirit. "
            "Disruptor, Razor, and Shadow Fiend are also good."
        )

    def test_mid_advantage(self):
        response, _ = ResponseGenerator.respond("Which mid heroes are good against Storm Spirit?")
        assert response.startswith(
            "<speak>Queen of Pain is very strong against Storm Spirit. "
            "Razor and Shadow Fiend are also good."
        )

    def test_two_hero_advantage(self):
        response, _ = ResponseGenerator.respond("Is Disruptor good against Storm Spirit?")
        assert "Disruptor's advantage is 1.75" in response


@pytest.mark.django_db
class TestFollowUpRespones(TestCase):
    def test_yes(self):
        AbilityFactory(
            name='Thunder Strike',
            cooldown='60/46/32/18',
            damage_type=DamageType.MAGICAL,
        )

        _, token = ResponseGenerator.respond('What is the cooldown of Thunder Strike?')
        response, token = ResponseGenerator.respond('Yes.', token)
        assert response == (
            '<speak>What would you like to know? '
            'You could ask about the cooldown or whether Thunder Strike goes through BKB.</speak>')
        response, token = ResponseGenerator.respond('What is its damage type>', token)
        assert 'magical' in response
        assert 'Anything else?' in response

    def test_no(self):
        AbilityFactory(name='Glimpse', cooldown='60/46/32/18')
        _, token = ResponseGenerator.respond('What is the cooldown of Glimpse?')
        _, token = ResponseGenerator.respond('Nope.', token)
        assert isinstance(Context.deserialise(token), FreshContext)

    def test_no_a_no(self):
        AbilityFactory(name='Glimpse', cooldown='60/46/32/18')
        _, token = ResponseGenerator.respond('What is the cooldown of Glimpse?')
        _, token = ResponseGenerator.respond('No.', token)
        with self.assertRaises(Goodbye):
            r, token = ResponseGenerator.respond('No.', token)

    def test_respond_to_fresh_context(self):
        AbilityFactory(name='Glimpse', cooldown='60/46/32/18')
        _, token = ResponseGenerator.respond('What is the cooldown of Glimpse?')
        _, token = ResponseGenerator.respond('No.', token)
        response, _ = ResponseGenerator.respond('What is the cooldown of Glimpse?', token)
        assert "cooldown" in response

    def test_no_ability_list(self):
        AbilityFactory(
            name='Glimpse',
            cooldown='60/46/32/18',
            hero=HeroFactory(name='Disruptor'),
        )
        _, token = ResponseGenerator.respond("What are Disruptor's abilities?")
        _, token = ResponseGenerator.respond('No.', token)
        assert isinstance(Context.deserialise(token), FreshContext)

    def test_no_counter_picking(self):
        storm_spirit = HeroFactory(name='Storm Spirit')
        queen_of_pain = HeroFactory(name='Queen of Pain')
        AdvantageFactory(hero=storm_spirit, enemy=queen_of_pain, advantage=1.75)
        _, token = ResponseGenerator.respond("What heroes are good against Queen of Pain")
        _, token = ResponseGenerator.respond('No.', token)
        assert isinstance(Context.deserialise(token), FreshContext)

    def test_changing_context(self):
        AbilityFactory(
            hero=HeroFactory(name='Disruptor'),
            name='Static Storm',
            cooldown='90/80/70',
            hotkey='R',
            is_ultimate=True,
        )

        _, token = ResponseGenerator.respond('What is the cooldown of Static Storm?')
        assert token['context-class'] == 'SingleAbilityContext'
        assert token['useage-count'] == 1

        response, token = ResponseGenerator.respond("What is Disruptor's ultimate?", token)
        assert "ultimate" in response
        assert "Static Storm" in response
        assert token['context-class'] == 'SingleAbilityContext'
        assert token['useage-count'] == 1

    def test_hero_advantage_remembers_hero(self):
        TestAdvantageParserAndResponders.setUpAdvantages()
        _, token = ResponseGenerator.respond("Which heroes are good against Storm Spirit?")
        response, _ = ResponseGenerator.respond("What about Sniper?", token)
        assert "-3.11" in response

    def test_hero_advantage_context_follow_up_with_role(self):
        TestAdvantageParserAndResponders.setUpAdvantages()
        _, token = ResponseGenerator.respond("Which heroes are good against Storm Spirit?")
        response, _ = ResponseGenerator.respond("Support", token)
        assert "Disruptor" in response
        assert "Queen of Pain" not in response

    def test_saying_against_breaks_hero_context(self):
        storm_spirit = HeroFactory(name='Storm Spirit')
        AbilityFactory(
            name='Glimpse',
            cooldown='60/46/32/18',
            hero=HeroFactory(name='Disruptor'),
        )
        AbilityFactory(
            name='Static Remnant',
            hero=storm_spirit,
        )
        AdvantageFactory(
            hero=HeroFactory(name='Queen of Pain'),
            enemy=storm_spirit,
            advantage=2.14,
        )
        _, token = ResponseGenerator.respond("Which are Disruptor's abilities?")
        response, _ = ResponseGenerator.respond("Who is good against Storm Spirit?", token)
        assert "Static Remnant" not in response
        assert "Queen of Pain" in response

    def test_saying_counters_breaks_old_counter_context(self):
        TestAdvantageParserAndResponders.setUpAdvantages()
        _, token = ResponseGenerator.respond("Which heroes are good against Queen of Pain?")
        response, _ = ResponseGenerator.respond("Who counters Storm Spirit?", token)
        assert "Disruptor" in response

    def test_question_with_conflicting_context_words(self):
        TestAdvantageParserAndResponders.setUpAdvantages()
        response, _ = ResponseGenerator.respond("not that strong what a Queen of Pain's abilities")
        assert 'Storm Spirit' in response
