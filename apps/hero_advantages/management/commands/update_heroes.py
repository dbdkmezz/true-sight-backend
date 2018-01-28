from django.core.management.base import BaseCommand, CommandError

from apps.hero_abilities.models import Ability
from apps.hero_advantages.models import Hero, Advantage


class Command(BaseCommand):
    help = 'Updates the heroes data by scraping the web'

    def handle(self, *args, **options):
        try:
            Hero.update_from_web()
            Advantage.update_from_web()
            Ability.update_from_web()
        except Exception as exc:
            raise CommandError('ERROR: {}'.format(exc))

        for h in Hero.objects.all():
            if Ability.objects.filter(hero=h, is_from_talent=False).count() < 4:
                print("{} doesn't have many abilities. The abilities I found are are: {}".format(
                    h, Ability.objects.filter(hero=h)))

        for h in Hero.objects.all():
            if Ability.objects.filter(hero=h, is_from_talent=False).count() > 4:
                print("{} has loads of abilities. The abilities I found are are: {}".format(
                    h, Ability.objects.filter(hero=h)))
        self.stdout.write(self.style.SUCCESS('Successfully updated heros'))
