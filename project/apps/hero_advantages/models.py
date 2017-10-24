from django.db import models


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

    @staticmethod
    def update_from_web():
        web_scraper = WebScraper()
        heroes = web_scraper.get_hero_names()
        pass


class Advantage(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE, related_name="hero_hero")
    enemy = models.ForeignKey(Hero, on_delete=models.CASCADE, related_name="enemy_hero")
    advantage = models.FloatField()

    class Meta:
        unique_together = ("hero", "enemy")

    def __str__(self):
        return "{}'s advntage over {} is {}".format(self.hero.name, self.enemy.name, self.advantage)

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
