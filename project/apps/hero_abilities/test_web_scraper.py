import py
import pytest

from django.test import TestCase

from ..utils.request_handler import MockRequestHandler
from ..hero_advantages.tests.factories import HeroFactory

from .web_scraper import WebScraper
from .models import Ability

mock_request_handler = MockRequestHandler(
    url_map={
        "https://dota2.gamepedia.com/Disruptor": "Disruptor - Dota 2 Wiki.html",
    },
    files_path=py.path.local().join("project", "apps", "hero_abilities", "test_data"),
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
        self.assertEqual(kinetic_field.cooldown, '13/12/11/10')
        self.assertEqual(kinetic_field.hotkey, 'E')
        self.assertFalse(kinetic_field.is_ultimate)

    def test_loads_ultimate(self):
        self.scraper.load_hero_abilities(HeroFactory(name='Disruptor'))
        self.assertTrue(Ability.objects.get(name='Static Storm').is_ultimate)
