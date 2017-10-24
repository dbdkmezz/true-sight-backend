from django.test import TestCase
from django.db import connection
from django.utils.encoding import force_text

from project.apps.hero_advantages.models import Hero, Advantage
from project.apps.hero_advantages.views import hero_list, hero_name, single_advantage

from .factories import HeroFactory


class TestViews(TestCase):
    def setup_heroes(self):
        HeroFactory(name="Joe")
        HeroFactory(name="Super-Bob")
        HeroFactory(name="Spacey Max")
        
    def test_hero_list(self):
        self.setup_heroes()
        response = hero_list(None)
        
        self.assertJSONEqual(
            force_text(response.content),
            {'Heroes': ["Joe", "Super-Bob", "Spacey Max"]},
        )
        
    def test_hero_name(self):
        self.setup_heroes()
        response = hero_name(None, 2)
        
        self.assertJSONEqual(
            force_text(response.content),
            {'Name': Hero.objects.filter(id=2).first().name},
        )

