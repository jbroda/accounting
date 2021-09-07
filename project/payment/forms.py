from django import forms
from django.conf import settings
import logging

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
class SetupForm(forms.Form):
    amount = forms.FloatField(initial='%.2f' % settings.ASSESSMENT, min_value=1.0)
    scheduling = forms.ChoiceField(choices=[('1','Single Payment'),
                                            ('2','Recurring Monthly Payment')])
    description = forms.CharField(widget=forms.Textarea(attrs={'rows':5}),
                                  initial="Please specify the address and number of your unit in here.")


