from registration.signals import user_registered
from registration.models import RegistrationProfile
from regsupplement.models import MyRegistrationSupplement
from accounting.models import Account
import logging

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
def register_signals():
    user_registered.connect(handle_user_registered)

##############################################################################
def handle_user_registered(sender, user, profile, request, **kwargs):
    logger.info("user: {0}, profile: {1}".format(user, profile))
    try:
        if profile.supplement_class:
            supplement_form_class = profile.supplement_class.get_form_class()
            supplement = supplement_form_class(request.POST)

        if supplement and supplement.is_valid():
            fn = supplement.cleaned_data.get('first_name')
            ln = supplement.cleaned_data.get('last_name')
            ph = supplement.cleaned_data.get('phone_number')
            acct_id = supplement.cleaned_data.get('account_id')

        logger.info("fn: {0}, ln: {1}, ph: {2}, acct: {3}".
                    format(fn, ln, ph, acct_id))

        user.first_name = fn
        user.last_name = ln
        user.phone_number = ph

        account = Account.objects.get(acct_id=acct_id)
        if account:
            for owner in account.owner_set.all():
                logger.info("Account {0} owner email: {1}".format(acct_id, owner.email))
                if user.email == owner.email:
                    user.owner = owner

        user.save()
    except Exception, e:
        logger.exception(e)

"""
from django import forms
from registration.forms import RegistrationForm
from localflavor.us.forms import USPhoneNumberField
from localflavor.us.models import PhoneNumberField
from registration.backends.default import DefaultRegistrationBackend
from django.db import models
from registration.supplements import RegistrationSupplementBase

##############################################################################
class MyRegistrationSupplement(RegistrationSupplementBase):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_numer = PhoneNumberField()
    unit_address = models.TextField()

    def __unicode__(self):
        # a summary of this supplement
        return "%s %s" % (self.first_name, self.last_name)

##############################################################################
class UserRegistrationForm(RegistrationForm):
    first_name = forms.CharField(max_length=200)
    last_name = forms.CharField(max_length=200)
    phone_numer = USPhoneNumberField()
    unit_address = forms.CharField(label='Unit Address(es)',widget=forms.Textarea(attrs={'rows':3}),
                                   initial="Please specify the address and number of your unit(s) in here.")

##############################################################################
class MyRegistrationBackend(DefaultRegistrationBackend):
    def get_registration_form_class(self):
        return UserRegistrationForm
"""
