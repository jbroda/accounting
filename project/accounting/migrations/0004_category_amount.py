# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_is_email_statement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='amount',
            field=models.DecimalField(null=True, verbose_name='Amount', max_digits=8, decimal_places=2, blank=True),
            preserve_default=True,
        ),
    ]
