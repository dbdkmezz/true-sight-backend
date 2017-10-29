from django.db import models

from .web_scraper import WebScraper, HeroRole


class Hero(models.Model):
    name = models.CharField(max_length=64, unique=True)
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
            print("ERROR: {} has not role".format(self.name))


class Advantage(models.Model):
    hero = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="hero_hero")
    enemy = models.ForeignKey(
        Hero, on_delete=models.CASCADE, related_name="enemy_hero")
    advantage = models.FloatField()

    class Meta:
        unique_together = ("hero", "enemy")

    def __str__(self):
        return "{}'s advntage over {} is {}".format(
            self.hero.name, self.enemy.name, self.advantage)

    @staticmethod
    def generate_info_dict(enemy_names):
        results = {}
        for h in Hero.objects.exclude(name__in=enemy_names):
            advantage = sum(a.advantage
                            for a in Advantage.objects.filter(hero=h)
                            if a.enemy.name in enemy_names)
            results[h.name] = h.generate_info_dict()
            results[h.name]['advantage'] = advantage
        return results

    @staticmethod
    def update_from_web():
        web_scraper = WebScraper()
        web_scraper.reset_cache()
        hero_names = list(web_scraper.get_hero_names())
        if len(hero_names) < 113:
            raise Exception("too few heroes got from the web")

        extra_heroes = Hero.objects.exclude(name__in=hero_names)
        for h in extra_heroes:
            print("Deleting {}".format(h.name))
            h.delete()

        for name in hero_names:
            print(name)
            hero, _ = Hero.objects.get_or_create(name=name)
            hero.update_from_web(web_scraper)
            hero.save()

        assert len(hero_names) == Hero.objects.count()

        print("\n\nLOADING ADVANTAGES\n")
        for hero in Hero.objects.all():
            print(hero.name)
            advantages_data = web_scraper.load_advantages_for_hero(hero.name)
            for advantage_data in advantages_data:
                print(Hero.objects.get(name=advantage_data['enemy_name']))
                try:
                    advantage = Advantage.objects.get(
                        hero=hero,
                        enemy=Hero.objects.get(name=advantage_data['enemy_name']),
                    )
                except Advantage.DoesNotExist:
                    Advantage.objects.create(
                        hero=hero,
                        enemy=Hero.objects.get(name=advantage_data['enemy_name']),
                        advantage=advantage_data['advantage'],
                    )
                else:
                    advantage.advantage = advantage_data['advantage']
                    advantage.save()
