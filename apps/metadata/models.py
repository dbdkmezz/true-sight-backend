import datetime

from django.db import models


class AdvantagesUpdate(models.Model):
    update_started = models.DateTimeField(default=datetime.datetime.now, unique=True)
    update_finished = models.DateTimeField(default=None, null=True, unique=True)

    @staticmethod
    def last_update():
        return AdvantagesUpdate.objects.order_by('update_started').last()

    @classmethod
    def last_update_time(cls):
        if AdvantagesUpdate.objects.count() == 0:
            return datetime.datetime(1970, 1, 1)
        return cls.last_update().update_started.replace(tzinfo=None)

    @classmethod
    def update_in_progress(cls):
        return cls.update_finished is None

    @classmethod
    def start_new_update(cls):
        AdvantagesUpdate.objects.create()

    @classmethod
    def finish_current_update(cls):
        last_update = cls.last_update()
        if last_update.update_finished:
            raise Exception("current update already finished")
        last_update.update_finished = datetime.datetime.now()
        last_update.save()
