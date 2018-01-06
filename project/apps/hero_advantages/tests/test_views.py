from django.test import TestCase
from django.utils.encoding import force_text

from project.apps.hero_advantages.models import Hero
from project.apps.hero_advantages.views import hero_list, hero_name, advantages

from .factories import HeroFactory, AdvantageFactory


class TestViews(TestCase):
    def setUp(self):
        joe = HeroFactory(name="Joe")
        sb = HeroFactory(name="Super-Bob")
        sm = HeroFactory(
            name="Spacey Max",
            is_carry=True,
            is_support=False,
            is_off_lane=True,
            is_jungler=False,
            is_mid=True,
            is_roaming=True,
        )
        r = HeroFactory(
            name="Rex",
            is_carry=False,
            is_support=True,
            is_off_lane=True,
            is_jungler=False,
            is_mid=False,
            is_roaming=True,
        )

        AdvantageFactory(hero=sm, enemy=joe, advantage=-0.5)
        AdvantageFactory(hero=sm, enemy=sb, advantage=-0.1)
        AdvantageFactory(hero=r, enemy=sb, advantage=3)
        AdvantageFactory(hero=r, enemy=joe, advantage=-1.2)

    def test_hero_list(self):
        response = hero_list(None)

        self.assertJSONEqual(
            force_text(response.content),
            {'Heroes': ["Joe", "Super-Bob", "Spacey Max", "Rex"]},
        )

    def test_hero_name(self):
        response = hero_name(None, 2)

        self.assertJSONEqual(
            force_text(response.content),
            {'Name': Hero.objects.filter(id=2).first().name},
        )

    def test_advantages(self):
        response = advantages(None, 'Joe/Super-Bob')
        print(response.content)
        self.assertJSONEqual(
            force_text(response.content),
            {'data':
             [
                 {
                     'advantages': [-0.5, -0.1],
                     'name': 'Spacey Max',
                     'is_jungler': False,
                     'is_carry': True,
                     'is_off_lane': True,
                     'is_support': False,
                     'is_roaming': True,
                     'is_mid': True,
                     'id_num': 3
                 },
                 {
                     'advantages': [-1.2, 3.0],
                     'name': 'Rex',
                     'is_jungler': False,
                     'is_carry': False,
                     'is_off_lane': True,
                     'is_support': True,
                     'is_roaming': True,
                     'is_mid': False,
                     'id_num': 4
                 }
             ]}
        )
