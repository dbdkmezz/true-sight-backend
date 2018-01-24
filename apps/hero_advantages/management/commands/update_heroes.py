from django.core.management.base import BaseCommand, CommandError

from ...models import Advantage


class Command(BaseCommand):
    help = 'Updates the heroes data by scraping the web'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        try:
            Advantage.update_from_web()
        except Exception as exc:
            raise CommandError('ERROR: {}'.format(exc))

        self.stdout.write(self.style.SUCCESS('Successfully updated heros'))
