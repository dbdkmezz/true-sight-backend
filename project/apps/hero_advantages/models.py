import logging

from django.db import models

from project.apps.metadata.models import AdvantagesUpdate

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

    def update_from_web(self, web_scraper):
        """Updates the hero's roles using the web scraper"""
        scraper = WebScraper()
        self.is_carry = scraper.hero_is_role(self.name, HeroRole.CARRY)
        self.is_support = scraper.hero_is_role(self.name, HeroRole.SUPPORT)
        self.is_off_lane = scraper.hero_is_role(self.name, HeroRole.OFF_LANE)
        self.is_jungler = scraper.hero_is_role(self.name, HeroRole.JUNGLER)
        self.is_mid = scraper.hero_is_role(self.name, HeroRole.MIDDLE)
        self.is_roaming = scraper.hero_is_role(self.name, HeroRole.ROAMING)

        if not (self.is_carry or self.is_support or self.is_off_lane
                or self.is_jungler or self.is_mid or self.is_roaming):
            logger.warning('Hero %s has no role', self.name)


class Advantage(models.Model):
    hero = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="hero_hero", db_index=True)
    enemy = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="enemy_hero", db_index=True)
    advantage = models.FloatField()

    class Meta:
        unique_together = ("hero", "enemy")

    def __str__(self):
        return "{}'s advntage over {} is {}".format(
            self.hero.name, self.enemy.name, self.advantage)

    @classmethod
    def generate_info_dict(cls, enemy_names):
        try:
            enemies = list(Hero.objects.get(name=enemy_name) for enemy_name in enemy_names)
        except Hero.DoesNotExist:
            logger.debug(
                'Attempting to generate_info_dict for invalid enemy names: %s', enemy_names)
            raise InvalidEnemyNames

        result = []
        for h in Hero.objects.exclude(pk__in=[e.pk for e in enemies]):
            advantages = list(
                Advantage.objects.get(hero=h, enemy=enemy).advantage
                for enemy in enemies
            )
            info_dict = h.generate_info_dict()
            info_dict['advantages'] = advantages
            result.append(info_dict)
        return result

    @staticmethod
    def update_from_web():
        AdvantagesUpdate.start_new_update()
        web_scraper = WebScraper()
        web_scraper.reset_cache()
        hero_names = list(web_scraper.get_hero_names())
        if len(hero_names) < 115:
            logger.warning('Got too few hero names from the web, only got %s', len(hero_names))
            raise Exception

        # Remove any heroes from the database which aren't in the new list
        extra_heroes = Hero.objects.exclude(name__in=hero_names)
        for h in extra_heroes:
            logger.warning('Removing %s from the heroes db', h.name)
            h.delete()

        for name in hero_names:
            hero, _ = Hero.objects.get_or_create(name=name)
            hero.update_from_web(web_scraper)
            hero.save()

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
