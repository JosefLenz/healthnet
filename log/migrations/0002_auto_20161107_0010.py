# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-11-07 00:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]
