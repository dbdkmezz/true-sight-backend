import py
import pytest

from django.test import TestCase

from apps.utils.request_handler import MockRequestHandler
from apps.hero_advantages.factories import HeroFactory

from .models import Ability, SpellImmunity, DamageType
from .web_scraper import WebScraper

mock_request_handler = MockRequestHandler(
    url_map={
        "https://dota2.gamepedia.com/Dark_Willow": "Dark Willow - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Disruptor": "Disruptor - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Pangolier": "Pangolier - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Phantom_Lancer": "Phantom Lancer - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Sniper": "Sniper - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Oracle": "Oracle - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Invoker": "Invoker - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Spectre": "Spectre - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Jakiro": "Jakiro - Dota 2 Wiki.html",
        "https://dota2.gamepedia.com/Keeper_of_the_Light": "Keeper of the Light - Dota 2 Wiki.html",
    },
    files_path=py.path.local().join("apps", "hero_abilities", "test_data"),
)


@pytest.mark.django_db
class TestWebScraper(TestCase):
    @property
    def scraper(self):
        return WebScraper(request_handler=mock_request_handler)

    def test_loads_all_abilities(self):
        disruptor = HeroFactory(name='Disruptor')
        self.scraper.load_hero_abilities(disruptor)

        self.assertEqual(Ability.objects.count(), 4)
        self.assertTrue(all(
            ability.hero == disruptor
            for ability in Ability.objects.all()
        ))

    def test_loads_kinetic_field(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Disruptor'))

        kinetic_field = Ability.objects.get(name='Kinetic Field')
        self.assertEqual(
            kinetic_field.description,
            "After a short formation time, creates a circular barrier of kinetic energy that "
            "enemies can't pass."
        )
        self.assertEqual(kinetic_field.cooldown, '13/12/11/10')
        self.assertEqual(kinetic_field.hotkey, 'E')
        self.assertFalse(kinetic_field.is_ultimate)
        self.assertEqual(kinetic_field.spell_immunity, SpellImmunity.DOES_NOT_PIERCE)
        self.assertEqual(kinetic_field.damage_type, None)
        self.assertEqual(kinetic_field.aghanims_damage_type, None)
        self.assertEqual(
            kinetic_field.spell_immunity_detail,
            "The Barrier's modifier persists if it was placed before spell immunity.")

    def test_loads_ultimate(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Disruptor'))
        self.assertTrue(Ability.objects.get(name='Static Storm').is_ultimate)

    def test_abilities_with_no_cooldown(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Phantom Lancer'))
        assert Ability.objects.get(name='Juxtapose').cooldown == ''

    @pytest.mark.skip("Talent abilities not yet implemented")
    def test_talent_abilities(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Phantom Lancer'))
        assert Ability.objects.get(name='Critical Strike').is_from_talent
        assert Ability.objects.filter(is_from_talent=False).count() == 4

    def test_abilities_with_long_headers(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Dark Willow'))
        for ability in Ability.objects.all():
            assert len(ability.hotkey) == 1

    def test_ignores_second_ability_with_same_hotkey(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Pangolier'))
        assert Ability.objects.count() == 4
        assert Ability.objects.get(name='Rolling Thunder')
        with self.assertRaises(Ability.DoesNotExist):
            assert Ability.objects.get(name='Stop Rolling')

    def test_damage_type_with_aghs(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Sniper'))
        assassinate = Ability.objects.get(name='Assassinate')
        self.assertEqual(assassinate.damage_type, DamageType.MAGICAL)
        self.assertEqual(assassinate.aghanims_damage_type, DamageType.PHYSICAL)

    def test_damage_type_with_talent(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Jakiro'))
        macropyre = Ability.objects.get(name='Macropyre')
        self.assertEqual(macropyre.damage_type, DamageType.MAGICAL)
        self.assertEqual(macropyre.aghanims_damage_type, None)

    def test_damage_type_with_hp_removal_detail(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Oracle'))
        false_promise = Ability.objects.get(name='False Promise')
        self.assertEqual(false_promise.damage_type, DamageType.PURE)
        self.assertIsNone(false_promise.aghanims_damage_type)

    def test_hp_removal_with_no_damage_type(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Spectre'))
        dispersion = Ability.objects.get(name='Dispersion')
        self.assertEqual(dispersion.damage_type, DamageType.PURE)
        self.assertIsNone(dispersion.aghanims_damage_type)

    def test_invoker_hotkeys(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Invoker'))
        for a in Ability.objects.all():
            assert (not a.hotkey or len(a.hotkey) == 1)

    # I think there may be an error on the dota wiki website,
    # I don't know the damange type of this spell, but lets deal with it better for now
    @pytest.mark.xfail
    def test_keeper_after_720(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Keeper of the Light'))
        illuminate = Ability.objects.get(name='Blinding Light')
        self.assertEqual(illuminate.damage_type, DamageType.MAGICAL)
