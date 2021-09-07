# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0002_account_is_no_statement'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntrySortedByAccount',
            fields=[
            ],
            options={
                'ordering': ('acct_id',),
                'verbose_name': 'Entry Sorted By Account',
                'proxy': True,
                'verbose_name_plural': 'Entries Sorted By Account',
            },
            bases=('accounting.account',),
        ),
        migrations.CreateModel(
            name='EntrySortedByDate',
            fields=[
            ],
            options={
                'ordering': ('-datetime',),
                'verbose_name': 'Entry Sorted By Date',
                'proxy': True,
                'verbose_name_plural': 'Entries Sorted By Date',
            },
            bases=('accounting.entry',),
        ),
        migrations.CreateModel(
            name='EntrySortedByTimestamp',
            fields=[
            ],
            options={
                'ordering': ('-timestamp',),
                'verbose_name': 'Entry Sorted By Timestamp',
                'proxy': True,
                'verbose_name_plural': 'Entries Sorted By Timestamp',
            },
            bases=('accounting.entry',),
        ),
        migrations.CreateModel(
            name='LeaseSortedByAccount',
            fields=[
            ],
            options={
                'ordering': ('account_id',),
                'proxy': True,
            },
            bases=('accounting.lease',),
        ),
        migrations.AlterModelOptions(
            name='account',
            options={'ordering': ['acct_id']},
        ),
        migrations.AddField(
            model_name='account',
            name='is_email_statement',
            field=models.BooleanField(default=False, verbose_name='E-Statement'),
            preserve_default=True,
        ),
    ]
