# Generated by Django 2.0.2 on 2018-02-22 21:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hero_abilities', '0007_auto_20180203_1444'),
    ]

    operations = [
        migrations.AddField(
            model_name='ability',
            name='aghanims_damage_type',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='ability',
            name='damage_type',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
