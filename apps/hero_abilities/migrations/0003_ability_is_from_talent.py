# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-28 19:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hero_abilities', '0002_auto_20180114_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='ability',
            name='is_from_talent',
            field=models.BooleanField(default=False),
        ),
    ]
