# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-08 11:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tagging', '0003_merge_20161003_1808'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='rubric',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='tag',
            name='en_name',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='en name'),
        ),
    ]
