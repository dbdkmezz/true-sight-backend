from django.test import TestCase
from django.utils.encoding import force_text

from project.apps.hero_advantages.models import Hero
from project.apps.hero_advantages.views import hero_list, hero_name

from .factories import HeroFactory


class TestViews(TestCase):
    def setUp(self):
        # don't know why I have to call this pytest should do this itself
        # must be something wrong with my config
        for h in Hero.objects.all():
            h.delete()

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

    # def test_hero_name(self):
    #     self.setup_heroes()
    #     response = hero_name(None, 2)

    #     self.assertJSONEqual(
    #         force_text(response.content),
    #         {'Name': Hero.objects.filter(id=2).first().name},
    #     )
