import logging

from django.core.management.base import BaseCommand, CommandError

from apps.hero_abilities.models import Ability
from apps.metadata.models import AdvantagesUpdate
from apps.hero_advantages.models import Hero, Advantage


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates the heroes data by scraping the web'

    def handle(self, *args, **options):
        try:
            AdvantagesUpdate.start_new_update()
            Hero.update_from_web()
            Advantage.update_from_web()
            Ability.update_from_web()
            AdvantagesUpdate.finish_current_update()
        except Exception as exc:
            raise CommandError('ERROR: {}'.format(exc))

        for hero in Hero.objects.all():
            if Ability.standard_objects.filter(hero=hero).count() < 4:
                logger.error(
                    "%s doesn't have many abilities. The abilities I found are are: %s",
                    hero,
                    Ability.standard_objects.filter(hero=hero))

        self.stdout.write(self.style.SUCCESS('Successfully updated heros'))
