# Generated by Django 2.0.2 on 2018-02-03 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0003_auto_20180203_1716'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyUse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True, unique=True)),
                ('total_uses', models.IntegerField(default=0)),
                ('total_successes', models.IntegerField(default=0)),
                ('total_failures', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='total_questions',
            field=models.IntegerField(default=1),
        ),
    ]