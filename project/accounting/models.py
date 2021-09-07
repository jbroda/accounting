from __future__ import unicode_literals
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
from localflavor.us.models import PhoneNumberField
from localflavor.us.models import USStateField
from hiddenpond.mixins import ChangeHistoryMixin
import logging
import re

##############################################################################
logger = logging.getLogger(__name__)

#############################################################################
class Account(ChangeHistoryMixin, models.Model):
    balance = models.DecimalField('Balance',max_digits=8,decimal_places=2)

    acct_id_regex = r'[BCP][0-9]{3,4}[1-6]{1}'
    acct_id = models.CharField('Account ID', 
                               max_length=10,
                               unique=True,
                               validators=[
                                RegexValidator(acct_id_regex,
                                               'Account ID format: ' + acct_id_regex,
                                               'Invalid Account ID'),])
    orig_id_regex = r'D[0-9]{5}'
    orig_id = models.CharField('Original ID', 
                               max_length=10,
                               unique=True,
                               validators=[
                                RegexValidator(orig_id_regex,
                                               'Original ID format: ' + orig_id_regex,
                                               'Invalid Original ID'),])

    unit_address_regex = r'\d{3,4} (Buccaneer Dr|Casey Ct|Pirates Cv)'
    unit_address = models.CharField('Unit Address', 
                                    max_length=20,
                                    validators=[
                                      RegexValidator(unit_address_regex,
                                                     'Unit address format: ' + unit_address_regex,
                                                     'Invalid Address'),])
    unit_number_regex = r'[1-6]{1}'
    unit_number = models.SmallIntegerField('Unit Number',
                                      validators=[
                                        RegexValidator(unit_number_regex,
                                                       'Unit number is between 1 and 6',
                                                       'Invalid Unit Number'),])
    pin_regex = r'\d{2}-\d{2}-\d{3}-\d{3}-\d{4}';
    pin = models.CharField('PIN',
                           max_length=18,
                           validators=[
                            RegexValidator(pin_regex,
                                           'PIN format: ' + pin_regex,
                                           'Invalid PIN'),])
    unit_regex = r'\d{1,2}-\d{2}'
    unit = models.CharField('Unit',
                            max_length=5,
                            validators=[
                             RegexValidator(unit_regex,
                                            'UNIT format: ' + unit_regex,
                                            'Invalid UNIT'),])

    is_payment_plan = models.BooleanField("Payment Plan", default=False)

    is_no_statement = models.BooleanField("No Statement", default=False)

    is_email_statement = models.BooleanField("E-Statement", default=False)

    @property
    def no_dashes_pin(self):
        return self.pin.replace('-','')

    @property
    def computed_balance(self):
        balance = 0
        for entry in self.entry_set.all():
            balance += entry.amount
        return balance

    @property
    def alt_acct_id1(self):
        match = re.search('(?P<first_letter>[BCP])(?P<number>[\d]{4,5})', self.acct_id)
        first_letter = match.group('first_letter')
        number = match.group('number')
        acct_id = None
        if first_letter == 'P':
            acct_id = 'PC' + number
        elif first_letter == 'B':
            acct_id = 'BD' + number
        elif first_letter == 'C':
            acct_id = 'CC' + number
        return acct_id

    @property
    def alt_acct_id2(self):
        match = re.search('(?P<first_letter>[BCP])(?P<number>[\d]{4,5})', self.acct_id)
        number = match.group('number')
        return  number

    def read_balance(self, datetime):
        balance = 0
        e = Entry.objects.filter( \
            account=self,datetime__lte=datetime).order_by("-datetime")[:1]
        if len(e) > 0:
            balance = e[0].balance

        return balance

    def __unicode__(self):
        return "{0} [{1}], Balance: {2}".format(self.acct_id, self.orig_id, self.balance)

    def get_absolute_url(self):
        return reverse('accounts:detail', kwargs={'pk' : self.pk})

    class Meta:
        ordering = ['acct_id']
    
##############################################################################
class Category(ChangeHistoryMixin, models.Model):
    # Supported charge names:
    LATE_FEE = 'Late Fee'
    POOL_DOOR_KEY_FEE = 'Pool Door Key Fee'
    ENTRY_DOOR_FEE = 'Entry Door Key Fee'
    TENNIS_COURT_KEY_FEE = 'Tennis Court Key Fee'
    LEASE_FINE = 'Lease Fine'
    RETURNED_CHECK_FEE = 'Returned Check Fee'
    LEGAL_FEE = 'Legal Fee'
    REPAIR_FEE = 'Repair Fee'
    MISC_FEE = 'Miscellaneous Fee'
    MISC_FINE = 'Miscellaneous Fine'

    # Supported charge types: payment (credit), charge, and assessment
    PAYMENT = 'PAID'
    CHARGE  = 'CHRG'
    ASSESSMENT = 'ASMT'
    TYPE_CHOICES = (
        (PAYMENT,'Payment / Credit'),
        (ASSESSMENT,'Assessment'),
        (CHARGE,'Charge'),
    )
    type = models.CharField('Type',max_length=4,choices=TYPE_CHOICES)
    is_visible = models.BooleanField(default=False)
    name = models.CharField('Name',max_length=50)
    amount = models.DecimalField('Amount',max_digits=8,decimal_places=2,blank=True,null=True)

    def __unicode__(self):
        return "%s: %s" % (self.type, self.name)

##############################################################################
class Entry(ChangeHistoryMixin, models.Model):
    user = models.CharField('User',max_length='50')
    datetime = models.DateTimeField('Date & Time')
    timestamp = models.DateTimeField('Timestamp')
    amount = models.DecimalField('Amount',max_digits=8,decimal_places=2)
    memo = models.CharField('Memo',max_length='200')
    category = models.ForeignKey(Category)
    account = models.ForeignKey(Account)
    balance = models.DecimalField('Balance',max_digits=8,decimal_places=2)

    def __unicode__(self):
        return ("%s | $%.2f | dt: %s | ts: %s | bal: %.2f | %s" % 
                (self.account.acct_id, self.amount, self.datetime, 
                 self.timestamp, self.balance, self.memo))

    class Meta:
        ordering = ['datetime','balance']
    
##############################################################################
class Person(ChangeHistoryMixin, models.Model):
    last_name = models.CharField('Last Name',max_length=200)
    first_name = models.CharField('First Name',max_length=200)
    middle_name = models.CharField('Middle Name',blank=True,max_length=200)
    home_phone = PhoneNumberField('Home Phone',blank=True)
    cell_phone = PhoneNumberField('Cell Phone',blank=True)
    email = models.EmailField(blank=True)

    def __unicode__(self):
        return "{0}, {1}".format(self.last_name, self.first_name)

    class Meta:
        abstract = True
        ordering = ['last_name']

##############################################################################
class Owner(Person):
    account = models.ManyToManyField(Account)
    address = models.CharField('Address', max_length=200)
    city = models.CharField('City', max_length=50)
    state = USStateField()
    zip = models.CharField('Zip',max_length=20)

    def get_absolute_url(self):
        return reverse('accounts:owner_detail', kwargs={'pk' : self.pk})

##############################################################################
def lease_file_name(instance, filename):
    return '/'.join([settings.LEASE_DIR, str(instance.account.orig_id), filename])

class Lease(ChangeHistoryMixin, models.Model):
    account = models.OneToOneField(Account)
    start_date = models.DateField('Start Date',blank=True,null=True)
    end_date = models.DateField('End Date',blank=True,null=True)
    monthly_rent = models.DecimalField('Monthly Rent',max_digits=8,decimal_places=2,null=True,blank=True)
    lease_file = models.FileField('Lease File',
                                  upload_to=lease_file_name,
                                  blank=True)

    def __unicode__(self):
        return "Lease for %s" % (self.account.acct_id)

##############################################################################
class Tenant(Person):
    lease = models.ForeignKey(Lease, null=True)
    is_owners_relative = models.BooleanField("Is a Relative of the Owner?", default=False, blank=True)

    def get_absolute_url(self):
        return reverse('accounts:tenant_detail', kwargs={'pk' : self.pk})

##############################################################################
class Vehicle(ChangeHistoryMixin, models.Model):
    account = models.ForeignKey(Account, null=True)
    year_make_and_model = models.CharField('Year, Make & Model',max_length=100)
    color = models.CharField('Color', max_length=50)
    license_plate = models.CharField('License Plate',max_length=20)

    def __unicode__(self):
        return ("Make: %s, Color: %s, License: %s" % 
                (self.year_make_and_model, self.color, self.license_plate))

    def get_absolute_url(self):
        return reverse('accounts:vehicle_detail', kwargs={'pk' : self.pk})

##############################################################################
class Report(models.Model):
    def __unicode__(self):
        return "mkm"

