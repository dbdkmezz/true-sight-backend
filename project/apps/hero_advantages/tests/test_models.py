import pytest
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings


from project.apps.metadata.models import AdvantagesUpdate
from project.apps.hero_advantages.models import Advantage, Hero
from project.apps.hero_advantages.exceptions import InvalidEnemyNames

from .factories import HeroFactory, AdvantageFactory


@pytest.mark.django_db
class TestModels(TestCase):
    def setUp(self):
        # don't know why I have to call this pytest should do this itself
        # must be something wrong with my config
        for h in Hero.objects.all():
            h.delete()
        for u in AdvantagesUpdate.objects.all():
            u.delete()

    def setup_advantages(self):
        joe = HeroFactory(name="Joe")
        sb = HeroFactory(name="Super-Bob", is_carry=True, is_jungler=False)
        sm = HeroFactory(name="Spacey Max", is_roaming=True)
        AdvantageFactory(hero=sb, enemy=joe, advantage=1.1)
        AdvantageFactory(hero=sm, enemy=joe, advantage=-0.5)
        AdvantageFactory(hero=joe, enemy=sb, advantage=2)
        AdvantageFactory(hero=sm, enemy=sb, advantage=-0.1)

    def test_single_info_dict(self):
        self.setup_advantages()
        result = list(Advantage.generate_info_dict(["Joe"]))
        self.assertEqual(len(list(result)), 2)

        sb = next(r for r in result if r['name'] == 'Super-Bob')
        self.assertEqual(sb["advantages"][0], 1.1)
        self.assertTrue(sb["is_carry"])
        self.assertFalse(sb["is_jungler"])

        sm = next(r for r in result if r['name'] == 'Spacey Max')
        self.assertEqual(sm["advantages"][0], -0.5)

    def test_info_dict_raises_invalid_enemy_names(self):
        self.setup_advantages()
        with self.assertRaises(InvalidEnemyNames):
            next(Advantage.generate_info_dict(["MADE UP HERO"]))

    def test_multi_hero_info_dict(self):
        self.setup_advantages()
        result = list(Advantage.generate_info_dict(["Joe", "Super-Bob"]))
        self.assertEqual(len(result), 1)
        sm = result[0]
        self.assertListEqual(sm["advantages"], [-0.5, -0.1])
        self.assertTrue(sm["is_roaming"], True)

    def test_multi_hero_info_dict_order_matters(self):
        self.setup_advantages()
        result = list(Advantage.generate_info_dict(["Super-Bob", "Joe"]))
        self.assertEqual(len(result), 1)
        sm = result[0]
        self.assertListEqual(sm["advantages"], [-0.1, -0.5])
        self.assertTrue(sm["is_roaming"], True)
