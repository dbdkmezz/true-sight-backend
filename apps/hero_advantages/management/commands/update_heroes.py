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

        self.stdout.write(self.style.SUCCESS('Successfully updated heros'))
