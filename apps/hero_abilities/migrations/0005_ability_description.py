# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-01 22:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hero_abilities', '0004_auto_20180201_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='ability',
            name='description',
            field=models.CharField(default='', max_length=1024),
            preserve_default=False,
        ),
    ]