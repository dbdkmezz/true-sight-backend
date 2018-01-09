import pytest
from django.test import TestCase

from project.apps.hero_advantages.models import Advantage
from project.apps.hero_advantages.exceptions import InvalidEnemyNames

from .factories import HeroFactory, AdvantageFactory


@pytest.mark.django_db
class TestModels(TestCase):
    def setUp(self):
        joe = HeroFactory(name="Joe")
        sb = HeroFactory(name="Super-Bob", is_carry=True, is_jungler=False)
        sm = HeroFactory(name="Spacey Max", is_roaming=True)
        AdvantageFactory(hero=sb, enemy=joe, advantage=1.1)
        AdvantageFactory(hero=sm, enemy=joe, advantage=-0.5)
        AdvantageFactory(hero=joe, enemy=sb, advantage=2)
        AdvantageFactory(hero=sm, enemy=sb, advantage=-0.1)

    def test_single_info_dict(self):
        result = Advantage.generate_info_dict(["Joe"])
        self.assertEqual(len(result), 2)

        sb = next(r for r in result if r['name'] == 'Super-Bob')
        self.assertEqual(sb["advantages"][0], 1.1)
        self.assertTrue(sb["is_carry"])
        self.assertFalse(sb["is_jungler"])

        sm = next(r for r in result if r['name'] == 'Spacey Max')
        self.assertEqual(sm["advantages"][0], -0.5)

    def test_info_dict_raises_invalid_enemy_names(self):
        with self.assertRaises(InvalidEnemyNames):
            Advantage.generate_info_dict(["MADE UP HERO"])

    def test_multi_hero_info_dict(self):
        result = Advantage.generate_info_dict(["Joe", "Super-Bob"])
        self.assertEqual(len(result), 1)
        sm = result[0]
        self.assertListEqual(sm["advantages"], [-0.5, -0.1])
        self.assertTrue(sm["is_roaming"], True)

    def test_multi_hero_info_dict_order_matters(self):
        result = Advantage.generate_info_dict(["Super-Bob", "Joe"])
        self.assertEqual(len(result), 1)
        sm = result[0]
        self.assertListEqual(sm["advantages"], [-0.1, -0.5])
        self.assertTrue(sm["is_roaming"], True)

    def test_multi_hero_info_dict_with_none(self):
        result = Advantage.generate_info_dict(["Joe", "none"])
        sb = next(r for r in result if r['name'] == "Super-Bob")
        self.assertEqual(sb["advantages"], [1.1, None])
        sm = next(r for r in result if r['name'] == "Spacey Max")
        self.assertListEqual(sm["advantages"], [-0.5, None])


@pytest.mark.django_db
class SimpleModelTestes(TestCase):
    """Tests which don't require the full db setup"""
    def test_nature_work_around(self):
        """There's a bug in the Android app which means that Nature's Prophet is just called Nature
        This tests we still give the correct result.
        """
        qop = HeroFactory(name="Queen of Pain")
        np = HeroFactory(name="Nature's Prophet")
        AdvantageFactory(hero=qop, enemy=np, advantage=1.2)
        result = Advantage.generate_info_dict(["Nature"])
        self.assertEqual(result[0]['name'], "Queen of Pain")
