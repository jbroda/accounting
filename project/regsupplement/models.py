from django import forms
from django.db import models
from localflavor.us.models import PhoneNumberField
from registration.supplements.base import RegistrationSupplementBase
from accounting.models import Account

"""
##############################################################################
class MyTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length, 
                    'widget': forms.Textarea(attrs={'rows':3})}
        defaults.update(kwargs)
        return super(MyTextField, self).formfield(**defaults)
"""

##############################################################################
class MyRegistrationSupplement(RegistrationSupplementBase):
    def get_account_choices():
        ACCOUNT_ID_CHOICES = ()
        try:
            for account in Account.objects.all():
                unit_address = "{0} Unit {1}".format(account.unit_address, account.unit_number)
                ACCOUNT_ID_CHOICES = ACCOUNT_ID_CHOICES + ((account.acct_id, unit_address),)

            # Sort by 'acct_id'.
            ACCOUNT_ID_CHOICES = sorted(ACCOUNT_ID_CHOICES, key=lambda entry: entry[0])
        except Exception, e:
            pass
        return ACCOUNT_ID_CHOICES

    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = PhoneNumberField()
    account_id = models.CharField(max_length=60,
                                  choices=get_account_choices(), 
                                  verbose_name='Unit address')

    def __unicode__(self):
        # a summary of this supplement
        return "%s %s" % (self.first_name, self.last_name)
