# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import localflavor.us.models
import accounting.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('balance', models.DecimalField(verbose_name='Balance', max_digits=8, decimal_places=2)),
                ('acct_id', models.CharField(unique=True, max_length=10, verbose_name='Account ID', validators=[django.core.validators.RegexValidator('[BCP][0-9]{3,4}[1-6]{1}', 'Account ID format: [BCP][0-9]{3,4}[1-6]{1}', 'Invalid Account ID')])),
                ('orig_id', models.CharField(unique=True, max_length=10, verbose_name='Original ID', validators=[django.core.validators.RegexValidator('D[0-9]{5}', 'Original ID format: D[0-9]{5}', 'Invalid Original ID')])),
                ('unit_address', models.CharField(max_length=20, verbose_name='Unit Address', validators=[django.core.validators.RegexValidator('\\d{3,4} (Buccaneer Dr|Casey Ct|Pirates Cv)', 'Unit address format: \\d{3,4} (Buccaneer Dr|Casey Ct|Pirates Cv)', 'Invalid Address')])),
                ('unit_number', models.SmallIntegerField(verbose_name='Unit Number', validators=[django.core.validators.RegexValidator('[1-6]{1}', 'Unit number is between 1 and 6', 'Invalid Unit Number')])),
                ('pin', models.CharField(max_length=18, verbose_name='PIN', validators=[django.core.validators.RegexValidator('\\d{2}-\\d{2}-\\d{3}-\\d{3}-\\d{4}', 'PIN format: \\d{2}-\\d{2}-\\d{3}-\\d{3}-\\d{4}', 'Invalid PIN')])),
                ('unit', models.CharField(max_length=5, verbose_name='Unit', validators=[django.core.validators.RegexValidator('\\d{1,2}-\\d{2}', 'UNIT format: \\d{1,2}-\\d{2}', 'Invalid UNIT')])),
                ('is_payment_plan', models.BooleanField(default=False, verbose_name='Payment Plan')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=4, verbose_name='Type', choices=[('PAID', 'Payment / Credit'), ('ASMT', 'Assessment'), ('CHRG', 'Charge')])),
                ('is_visible', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('amount', models.DecimalField(verbose_name='Amount', max_digits=8, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length='50', verbose_name='User')),
                ('datetime', models.DateTimeField(verbose_name='Date & Time')),
                ('timestamp', models.DateTimeField(verbose_name='Timestamp')),
                ('amount', models.DecimalField(verbose_name='Amount', max_digits=8, decimal_places=2)),
                ('memo', models.CharField(max_length='200', verbose_name='Memo')),
                ('balance', models.DecimalField(verbose_name='Balance', max_digits=8, decimal_places=2)),
                ('account', models.ForeignKey(to='accounting.Account')),
                ('category', models.ForeignKey(to='accounting.Category')),
            ],
            options={
                'ordering': ['datetime', 'balance'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField(null=True, verbose_name='Start Date', blank=True)),
                ('end_date', models.DateField(null=True, verbose_name='End Date', blank=True)),
                ('monthly_rent', models.DecimalField(null=True, verbose_name='Monthly Rent', max_digits=8, decimal_places=2, blank=True)),
                ('lease_file', models.FileField(upload_to=accounting.models.lease_file_name, verbose_name='Lease File', blank=True)),
                ('account', models.OneToOneField(to='accounting.Account')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_name', models.CharField(max_length=200, verbose_name='Last Name')),
                ('first_name', models.CharField(max_length=200, verbose_name='First Name')),
                ('middle_name', models.CharField(max_length=200, verbose_name='Middle Name', blank=True)),
                ('home_phone', localflavor.us.models.PhoneNumberField(max_length=20, verbose_name='Home Phone', blank=True)),
                ('cell_phone', localflavor.us.models.PhoneNumberField(max_length=20, verbose_name='Cell Phone', blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('address', models.CharField(max_length=200, verbose_name='Address')),
                ('city', models.CharField(max_length=50, verbose_name='City')),
                ('state', localflavor.us.models.USStateField(max_length=2, choices=[(b'AL', b'Alabama'), (b'AK', b'Alaska'), (b'AS', b'American Samoa'), (b'AZ', b'Arizona'), (b'AR', b'Arkansas'), (b'AA', b'Armed Forces Americas'), (b'AE', b'Armed Forces Europe'), (b'AP', b'Armed Forces Pacific'), (b'CA', b'California'), (b'CO', b'Colorado'), (b'CT', b'Connecticut'), (b'DE', b'Delaware'), (b'DC', b'District of Columbia'), (b'FL', b'Florida'), (b'GA', b'Georgia'), (b'GU', b'Guam'), (b'HI', b'Hawaii'), (b'ID', b'Idaho'), (b'IL', b'Illinois'), (b'IN', b'Indiana'), (b'IA', b'Iowa'), (b'KS', b'Kansas'), (b'KY', b'Kentucky'), (b'LA', b'Louisiana'), (b'ME', b'Maine'), (b'MD', b'Maryland'), (b'MA', b'Massachusetts'), (b'MI', b'Michigan'), (b'MN', b'Minnesota'), (b'MS', b'Mississippi'), (b'MO', b'Missouri'), (b'MT', b'Montana'), (b'NE', b'Nebraska'), (b'NV', b'Nevada'), (b'NH', b'New Hampshire'), (b'NJ', b'New Jersey'), (b'NM', b'New Mexico'), (b'NY', b'New York'), (b'NC', b'North Carolina'), (b'ND', b'North Dakota'), (b'MP', b'Northern Mariana Islands'), (b'OH', b'Ohio'), (b'OK', b'Oklahoma'), (b'OR', b'Oregon'), (b'PA', b'Pennsylvania'), (b'PR', b'Puerto Rico'), (b'RI', b'Rhode Island'), (b'SC', b'South Carolina'), (b'SD', b'South Dakota'), (b'TN', b'Tennessee'), (b'TX', b'Texas'), (b'UT', b'Utah'), (b'VT', b'Vermont'), (b'VI', b'Virgin Islands'), (b'VA', b'Virginia'), (b'WA', b'Washington'), (b'WV', b'West Virginia'), (b'WI', b'Wisconsin'), (b'WY', b'Wyoming')])),
                ('zip', models.CharField(max_length=20, verbose_name='Zip')),
                ('account', models.ManyToManyField(to='accounting.Account')),
            ],
            options={
                'ordering': ['last_name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_name', models.CharField(max_length=200, verbose_name='Last Name')),
                ('first_name', models.CharField(max_length=200, verbose_name='First Name')),
                ('middle_name', models.CharField(max_length=200, verbose_name='Middle Name', blank=True)),
                ('home_phone', localflavor.us.models.PhoneNumberField(max_length=20, verbose_name='Home Phone', blank=True)),
                ('cell_phone', localflavor.us.models.PhoneNumberField(max_length=20, verbose_name='Cell Phone', blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('is_owners_relative', models.BooleanField(default=False, verbose_name='Is a Relative of the Owner?')),
                ('lease', models.ForeignKey(to='accounting.Lease', null=True)),
            ],
            options={
                'ordering': ['last_name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year_make_and_model', models.CharField(max_length=100, verbose_name='Year, Make & Model')),
                ('color', models.CharField(max_length=50, verbose_name='Color')),
                ('license_plate', models.CharField(max_length=20, verbose_name='License Plate')),
                ('account', models.ForeignKey(to='accounting.Account', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
