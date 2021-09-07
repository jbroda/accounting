from django import forms
from django.conf import settings
from django.forms import ModelForm
from localflavor.us.forms import USZipCodeField
from .models import Account, Entry, Category, Owner, Lease, Tenant, Vehicle, Report
import logging
import sys

logger = logging.getLogger(__name__)

##############################################################################
class AccountEntryForm(forms.Form):
    category_choices = []
    try:
        categories = Category.objects.all()
        category_choices = [(o.name, o.type) for o in categories if categories]
    except Exception,e:
        logging.exception(e)
    amount = forms.DecimalField()
    memo = forms.CharField()
    category = forms.ChoiceField(choices=category_choices)
    date = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS)
    accounts = forms.BooleanField(
        error_messages={ 
           'required':'Please specify one more more accounts',
        })

    def clean(self):
        cleaned_data = super(AccountEntryForm, self).clean()
        amount = cleaned_data.get('amount')
        category = cleaned_data.get('category')
        if amount and category:
            category_type = Category.objects.get(name=category).type
            if (amount < 0 and category_type == Category.CHARGE or
                amount > 0 and category_type == Category.PAYMENT):
                msg = u"Please enter a positive amount for a charge, negative for a payment!"
                self._errors['amount'] = self.error_class([msg])
                self._errors['category'] = self.error_class([msg])
                del cleaned_data['amount']
                del cleaned_data['category']

        return cleaned_data

##############################################################################
class AccountForm(ModelForm):
    class Meta:
        model = Account
        exclude = ['balance','acct_id','orig_id','pin','unit']

##############################################################################
class EntryForm(ModelForm):
    class Meta:
        model = Entry
        fields = ['memo']

##############################################################################
class OwnerForm(ModelForm):
    zip = USZipCodeField()

    class Meta:
        model = Owner
        fields = '__all__'

##############################################################################
class Html5DateInput(forms.DateInput):
    input_type = 'date'

##############################################################################
class TenantForm(ModelForm):
    class Meta:
        model = Tenant
        fields = '__all__'

##############################################################################
class LeaseForm(ModelForm):
    class Meta:
        model = Lease
        fields = '__all__'

##############################################################################
class VehicleForm(ModelForm):
    class Meta:
        model = Vehicle
        fields = '__all__'

##############################################################################
class ReportForm(ModelForm):
    date = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS)

    class Meta:
        model = Report 
        fields = '__all__'

