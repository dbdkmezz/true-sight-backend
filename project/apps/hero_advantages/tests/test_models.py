from django.test import TestCase
from django.db import connection

from project.apps.hero_advantages.models import Hero, Advantage

from .factories import HeroFactory, AdvantageFactory


class TestModels(TestCase):
    def setup_advantages(self):
        connection.creation.create_test_db()
        joe = HeroFactory(name="Joe")
        sb = HeroFactory(name="Super-Bob", is_carry=True, is_jungler=False)
        sm = HeroFactory(name="Spacey Max", is_roaming=True)
        AdvantageFactory(hero=sb, enemy=joe, advantage=1.1)
        AdvantageFactory(hero=sm, enemy=joe, advantage=-0.5)
        AdvantageFactory(hero=joe, enemy=sb, advantage=2)
        AdvantageFactory(hero=sm, enemy=sb, advantage=-0.1)

    def test_single_info_dict(self):
        self.setup_advantages()
        result = Advantage.generate_info_dict(["Joe"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result["Super-Bob"]["advantage"], 1.1)
        self.assertTrue(result["Super-Bob"]["is_carry"])
        self.assertFalse(result["Super-Bob"]["is_jungler"])
        self.assertEqual(result["Spacey Max"]["advantage"], -0.5)

    def test_multi_hero_info_dict(self):
        self.setup_advantages()
        result = Advantage.generate_info_dict(["Joe", "Super-Bob"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result["Spacey Max"]["advantage"], -0.6)
        self.assertEqual(result["Spacey Max"]["is_roaming"], True)
