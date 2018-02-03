from enum import IntEnum, unique
from django.db import models

from apps.hero_advantages.models import Hero


@unique
class SpellImmunity(IntEnum):
    PIERCES = 1
    PARTIALLY_PIERCES = 2
    DOES_NOT_PIERCE = 3


class StandardAbilityManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_from_talent=False,
            is_from_aghanims=False,
        )


class Ability(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=64, db_index=True)
    description = models.CharField(max_length=1024)
    cooldown = models.CharField(max_length=64, blank=True)
    hotkey = models.CharField(max_length=1)
    is_ultimate = models.BooleanField(default=False)
    is_from_talent = models.BooleanField(default=False)  # not currently used
    is_from_aghanims = models.BooleanField(default=False)  # not currently used
    spell_immunity = models.IntegerField(null=True, blank=True, default=None)
    spell_immunity_detail = models.CharField(max_length=512, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    standard_objects = StandardAbilityManager()

    class Meta:
        unique_together = ('hero', 'name')

    def __str__(self):
        return self.name

    @staticmethod
    def update_from_web(request_handler=None):
        from .web_scraper import WebScraper  # avoid circual dependency, eugh!
        web_scraper = WebScraper(request_handler)
        for hero in Hero.objects.all():
            web_scraper.load_hero_abilities(hero)
