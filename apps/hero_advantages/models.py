import logging

from django.db import models

from apps.metadata.models import AdvantagesUpdate

from .exceptions import InvalidEnemyNames
from .web_scraper import WebScraper, HeroRole


logger = logging.getLogger(__name__)


class Hero(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    is_carry = models.BooleanField(default=False)
    is_support = models.BooleanField(default=False)
    is_off_lane = models.BooleanField(default=False)
    is_jungler = models.BooleanField(default=False)
    is_mid = models.BooleanField(default=False)
    is_roaming = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def generate_info_dict(self):
        return {
            'name': self.name,
            'id_num': self.pk,
            'is_carry': self.is_carry,
            'is_support': self.is_support,
            'is_off_lane': self.is_off_lane,
            'is_jungler': self.is_jungler,
            'is_mid': self.is_mid,
            'is_roaming': self.is_roaming,
        }

    def update_roles(self, web_scraper):
        """Updates the hero's roles using the web scraper"""
        self.is_carry = web_scraper.hero_is_role(self.name, HeroRole.CARRY)
        self.is_support = web_scraper.hero_is_role(self.name, HeroRole.SUPPORT)
        self.is_off_lane = web_scraper.hero_is_role(self.name, HeroRole.OFF_LANE)
        self.is_jungler = web_scraper.hero_is_role(self.name, HeroRole.JUNGLER)
        self.is_mid = web_scraper.hero_is_role(self.name, HeroRole.MIDDLE)
        self.is_roaming = web_scraper.hero_is_role(self.name, HeroRole.ROAMING)

        if not (self.is_carry or self.is_support or self.is_off_lane
                or self.is_jungler or self.is_mid or self.is_roaming):
            logger.warning('Hero %s has no role', self.name)

    @staticmethod
    def update_from_web(request_handler=None):
        web_scraper = WebScraper(request_handler)
        hero_names = list(web_scraper.get_hero_names())

        # Remove any heroes from the database which aren't in the new list
        extra_heroes = Hero.objects.exclude(name__in=hero_names)
        for hero in extra_heroes:
            logger.warning('Removing the hero %s from the database', hero)
            hero.delete()

        for name in hero_names:
            hero, _ = Hero.objects.get_or_create(name=name)
            hero.update_roles(web_scraper)
            hero.save()


class Advantage(models.Model):
    hero = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="hero_hero", db_index=True)
    enemy = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="enemy_hero", db_index=True)
    advantage = models.FloatField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("hero", "enemy")

    def __str__(self):
        return "{}'s advntage over {} is {}".format(
            self.hero.name, self.enemy.name, self.advantage)

    @classmethod
    def generate_info_dict(cls, enemy_names):
        enemy_names = cls._nature_bug_workaround(enemy_names)
        try:
            enemies = [
                Hero.objects.get(name=enemy_name) if enemy_name != 'none' else None
                for enemy_name in enemy_names
            ]
        except Hero.DoesNotExist:
            logger.debug(
                'Attempting to generate_info_dict for invalid enemy names: %s', enemy_names)
            raise InvalidEnemyNames

        result = []
        for h in Hero.objects.exclude(pk__in=[e.pk for e in enemies if e]):
            advantages = list(
                Advantage.objects.get(hero=h, enemy=enemy).advantage if enemy else None
                for enemy in enemies
            )
            info_dict = h.generate_info_dict()
            info_dict['advantages'] = advantages
            result.append(info_dict)
        return result

    @staticmethod
    def _nature_bug_workaround(enemy_names):
        return [
            "Nature's Prophet" if e == "Nature" else e
            for e in enemy_names
        ]

    @staticmethod
    def update_from_web(request_handler=None):
        web_scraper = WebScraper(request_handler)
        for hero in Hero.objects.all():
            advantages_data = web_scraper.load_advantages_for_hero(hero.name)
            for advantage_data in advantages_data:
                adv = advantage_data['advantage']
                enemy = Hero.objects.get(name=advantage_data['enemy_name'])
                Advantage.objects.update_or_create(
                    hero=hero,
                    enemy=enemy,
                    defaults={'advantage': adv},
                )

        AdvantagesUpdate.finish_current_update()
