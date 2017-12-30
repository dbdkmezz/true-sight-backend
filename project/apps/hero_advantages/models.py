import time
import datetime
import threading
from django.db import models
from django.conf import settings

from project.apps.metadata.models import AdvantagesUpdate

from .exceptions import InvalidEnemyNames
from .web_scraper import WebScraper, HeroRole


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
        t = time.time()
        scraper = WebScraper()
        print("  update scraper {}".format(time.time() - t))
        t = time.time()
        self.is_carry = scraper.hero_is_role(self.name, HeroRole.CARRY)
        self.is_support = scraper.hero_is_role(self.name, HeroRole.SUPPORT)
        self.is_off_lane = scraper.hero_is_role(self.name, HeroRole.OFF_LANE)
        self.is_jungler = scraper.hero_is_role(self.name, HeroRole.JUNGLER)
        self.is_mid = scraper.hero_is_role(self.name, HeroRole.MIDDLE)
        self.is_roaming = scraper.hero_is_role(self.name, HeroRole.ROAMING)
        print("  load deatails {}".format(time.time() - t))

        if not (self.is_carry or self.is_support or self.is_off_lane
                or self.is_jungler or self.is_mid or self.is_roaming):
            print("ERROR: {} has not role".format(self.name))


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
        if Hero.objects.count() == 0:
            cls._start_update_if_due()

        enemies = Hero.objects.filter(name__in=enemy_names)
        if len(enemies) != len(enemy_names):
            raise InvalidEnemyNames
        results = []
        for h in Hero.objects.exclude(pk__in=[e.pk for e in enemies]):
            advantage = sum(a.advantage for a in Advantage.objects.filter(hero=h, enemy__in=enemies))
            info_dict = h.generate_info_dict()
            info_dict['advantages'] = [advantage]  # this won't work for more than one!
            results.append(info_dict)

        if getattr(settings, 'DISABLE_THREADING', None):
            cls._start_update_if_due()
        else:
            thread = threading.Thread(target=cls._start_update_if_due)
            thread.start()

        return results

    @classmethod
    def _start_update_if_due(cls):
        if not AdvantagesUpdate.update_in_progress():
            if (datetime.datetime.now() - AdvantagesUpdate.last_update_time()).total_seconds() > 86400:
                AdvantagesUpdate.start_new_update()
                cls.update_from_web()
                AdvantagesUpdate.finish_current_update()

    @staticmethod
    def update_from_web():
        web_scraper = WebScraper()
        web_scraper.reset_cache()
        hero_names = list(web_scraper.get_hero_names())
        if len(hero_names) < 115:
            raise Exception("too few heroes got from the web")

        # Remove any heroes from the database which aren't in the new list
        extra_heroes = Hero.objects.exclude(name__in=hero_names)
        for h in extra_heroes:
            print("Deleting {}".format(h.name))
            h.delete()

        for name in hero_names:
            print(name)
            t = time.time()
            hero, _ = Hero.objects.get_or_create(name=name)
            print("  get_or_create {}".format(time.time() - t))
            t = time.time()
            hero.update_from_web(web_scraper)
            print("  update_from_web {}".format(time.time() - t))
            t = time.time()
            hero.save()
            print("  save {}".format(time.time() - t))

        assert len(hero_names) == Hero.objects.count()

        print("\n\nLOADING ADVANTAGES\n")
        for hero in Hero.objects.all():
            print(hero)
            advantages_data = web_scraper.load_advantages_for_hero(hero.name)
            for advantage_data in advantages_data:
                print("  {}".format(advantage_data['enemy_name']))
                t = time.time()
                adv = advantage_data['advantage']
                print("    get adv {}".format(time.time() - t))
                t = time.time()
                enemy = Hero.objects.get(name=advantage_data['enemy_name'])
                print("    get enemy {} {}".format(enemy, time.time() - t))
                t = time.time()
                Advantage.objects.update_or_create(
                    hero=hero,
                    enemy=enemy,
                    defaults={'advantage': adv},
                )
                print("    update_or_create {}".format(time.time() - t))
                t = time.time()
