import json
import logging

from django.core.management.base import BaseCommand

from apps.hero_advantages.models import Hero


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prints json of the heroes, for use by Google Assistant SDK'

    def handle(self, *args, **options):
        result = []
        for hero in Hero.objects.all():
            result.append({
                'key': hero.name,
                'synonyms': hero.aliases,
            })

        result = {'entities': result}
        self.stdout.write(json.dumps(result))
        self.stdout.write(self.style.SUCCESS('Successfully updated heros'))
