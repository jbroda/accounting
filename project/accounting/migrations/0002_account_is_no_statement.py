# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='is_no_statement',
            field=models.BooleanField(default=False, verbose_name='No Statement'),
            preserve_default=True,
        ),
    ]
