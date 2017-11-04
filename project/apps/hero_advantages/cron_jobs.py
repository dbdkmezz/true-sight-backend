from django_cron import CronJobBase, Schedule

from .models import Advantage


class Update(CronJobBase):
    RUN_EVERY_MINS = 720  # every 12 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'hero_advantages.update'

    def do(self):
        Advantage.update_from_web()
