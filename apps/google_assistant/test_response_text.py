import pytest

from django.test import TestCase

from apps.hero_advantages.roles import HeroRole
from apps.hero_advantages.factories import HeroFactory, AdvantageFactory
from apps.hero_abilities.factories import AbilityFactory

from .response_text import (
    AbilityCooldownResponse, AbilityListResponse, SingleHeroCountersResponse,
    SingleHeroAdvantagesResponse,
)


@pytest.mark.django_db
class TestReponses(TestCase):
    def test_when_no_cooldown(self):
        ability = AbilityFactory(
            hero=HeroFactory(name='Pangolier'),
            name='Swashbuckle',
            cooldown='',
        )
        response = AbilityCooldownResponse.respond(ability, user_id=None)
        assert response == "Swashbuckle is a passive ability, with no cooldown"

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

        response = AbilityListResponse.respond(phantom_lancer, user_id=None)
        assert 'Juxtapose' in response
        assert 'Critical Strike' not in response

    def test_counter_respones(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        AdvantageFactory(
            hero=HeroFactory(name='Meepo'),
            enemy=queen_of_pain,
            advantage=4.34,
        )

        response = SingleHeroCountersResponse.respond(queen_of_pain, role=None, user_id=None)
        assert response == 'Meepo is very strong against Queen of Pain'

    def test_counter_role_response(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        AdvantageFactory(
            hero=HeroFactory(name='Meepo', is_support=False),
            enemy=queen_of_pain,
            advantage=4.34,
        )
        AdvantageFactory(
            hero=HeroFactory(name='Oracle', is_support=True),
            enemy=queen_of_pain,
            advantage=1.4,
        )
        response = SingleHeroCountersResponse.respond(
            queen_of_pain, role=HeroRole.SUPPORT, user_id=None)
        assert response == "Oracle is good against Queen of Pain"

    def test_counter_response_no_matching_hero(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        response = SingleHeroCountersResponse.respond(
            queen_of_pain, role=HeroRole.JUNGLER, user_id=None)
        assert response == (
            "Sorry, I don't know of any jungle heroes which counter Queen of Pain")

    def test_strengths_response(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        storm_spirit = HeroFactory(name='Storm Spirit')
        AdvantageFactory(hero=queen_of_pain, enemy=storm_spirit, advantage=1.75)

        response = SingleHeroAdvantagesResponse.respond(queen_of_pain, role=None, user_id=None)
        assert response == 'Queen of Pain is good against Storm Spirit'

    def test_strengths_role_response(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        storm_spirit = HeroFactory(name='Storm Spirit', is_support=False)
        keeper = HeroFactory(name='Keeper of the Light', is_support=True)
        AdvantageFactory(hero=queen_of_pain, enemy=storm_spirit, advantage=1.75)
        AdvantageFactory(hero=queen_of_pain, enemy=keeper, advantage=1.52)

        response = SingleHeroAdvantagesResponse.respond(
            queen_of_pain, role=HeroRole.SUPPORT, user_id=None)
        assert response == 'Queen of Pain is good against Keeper of the Light'

    def test_strengths_response_no_matching_hero(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        response = SingleHeroAdvantagesResponse.respond(
            queen_of_pain, role=HeroRole.JUNGLER, user_id=None)
        assert response == (
            "Sorry, I don't know of any jungle heroes which Queen of Pain counters")

    def test_extreme_strengths_response(self):
        queen_of_pain = HeroFactory(name='Queen of Pain')
        AdvantageFactory(
            hero=queen_of_pain,
            enemy=HeroFactory(name='Storm Spirit'),
            advantage=1.75)
        AdvantageFactory(
            hero=queen_of_pain,
            enemy=HeroFactory(name='Clockwerk'),
            advantage=2.58)

        response = SingleHeroAdvantagesResponse.respond(queen_of_pain, role=None, user_id=None)
        assert response == (
            'Queen of Pain is very strong against Clockwerk, and also counters Storm Spirit')
