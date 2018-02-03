from django.db import models
from django.utils import timezone


class AdvantagesUpdate(models.Model):
    update_started = models.DateTimeField(default=timezone.now, unique=True)
    update_finished = models.DateTimeField(default=None, null=True, unique=True)

    @staticmethod
    def last_update():
        return AdvantagesUpdate.objects.order_by('update_started').last()

    @classmethod
    def last_update_time(cls):
        if AdvantagesUpdate.objects.count() == 0:
            return timezone.datetime(1970, 1, 1)
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
        last_update.update_finished = timezone.datetime.now()
        last_update.save()


class User(models.Model):
    user_id = models.CharField(max_length=128, unique=True, db_index=True)
    total_questions = models.IntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @staticmethod
    def log_user(user_id):
        if not User.objects.filter(user_id=user_id).exists():
            User.objects.create(user_id=user_id)
        else:
            User.objects.filter(
                user_id=user_id
            ).update(
                total_questions=models.F('total_questions') + 1,
                date_modified=timezone.now(),
            )


class DailyUse(models.Model):
    date = models.DateField(unique=True, db_index=True)
    total_uses = models.IntegerField(default=0)
    total_successes = models.IntegerField(default=0)
    total_failures = models.IntegerField(default=0)

    @staticmethod
    def log_use(success):
        today = timezone.datetime.today()
        if not DailyUse.objects.filter(date=today).exists():
            DailyUse.objects.create(date=today)
        DailyUse.objects.filter(date=today).update(
            total_uses=models.F('total_uses') + 1,
            total_successes=models.F('total_successes') + (1 if success else 0),
            total_failures=models.F('total_failures') + (0 if success else 1),
        )


class ResponderUse(models.Model):
    responder = models.CharField(max_length=32, db_index=True)
    total_uses = models.IntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @staticmethod
    def log_use(responder):
        if not ResponderUse.objects.filter(responder=responder).exists():
            ResponderUse.objects.create(responder=responder)
        else:
            ResponderUse.objects.filter(
                responder=responder
            ).update(
                total_uses=models.F('total_uses') + 1,
                date_modified=timezone.now(),
            )
