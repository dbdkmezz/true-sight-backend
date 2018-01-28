from django.db import models

from apps.hero_advantages.models import Hero

from .web_scraper import WebScraper


class Ability(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=64, db_index=True)
    cooldown = models.CharField(max_length=64)
    hotkey = models.CharField(max_length=1)
    is_ultimate = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hero', 'name')

    def __str__(self):
        return self.name

    @staticmethod
    def update_from_web(request_handler=None):
        web_scraper = WebScraper(request_handler)
        for hero in Hero.objects.all():
            web_scraper.load_hero_abilities(hero)
