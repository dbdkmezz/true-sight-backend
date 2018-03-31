import pytest

from django.test import TestCase

from apps.hero_advantages.factories import HeroFactory
from apps.hero_abilities.factories import AbilityFactory

from .response import AbilityCooldownResponse, AbilityListResponse


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
