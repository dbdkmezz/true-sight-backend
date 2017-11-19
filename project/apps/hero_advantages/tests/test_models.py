import time
import pytest
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings


from project.apps.metadata.models import AdvantagesUpdate
from project.apps.hero_advantages.models import Advantage, Hero

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
        with patch.object(Advantage, '_start_update_if_due') as start_update:
            result = Advantage.generate_info_dict(["Joe"])
            assert start_update.call_count == 1
        self.assertEqual(len(result), 2)
        self.assertEqual(result["Super-Bob"]["advantage"], 1.1)
        self.assertTrue(result["Super-Bob"]["is_carry"])
        self.assertFalse(result["Super-Bob"]["is_jungler"])
        self.assertEqual(result["Spacey Max"]["advantage"], -0.5)

    def test_multi_hero_info_dict(self):
        self.setup_advantages()
        with patch.object(Advantage, '_start_update_if_due') as start_update:
            result = Advantage.generate_info_dict(["Joe", "Super-Bob"])
            assert start_update.call_count == 1
        self.assertEqual(len(result), 1)
        self.assertEqual(result["Spacey Max"]["advantage"], -0.6)
        self.assertEqual(result["Spacey Max"]["is_roaming"], True)

    def test_starts_update_if_no_heroes(self):
        with patch.object(Advantage, 'update_from_web', side_effect=self.setup_advantages) as update_from_web:
            Advantage.generate_info_dict(["Joe"])
            assert update_from_web.call_count == 1

    def test_starts_if_never_updated(self):
        settings.DISABLE_THREADING = True
        self.setup_advantages()
        with patch.object(Advantage, 'update_from_web') as update_from_web:
            Advantage.generate_info_dict(["Joe"])
            assert update_from_web.call_count == 1
