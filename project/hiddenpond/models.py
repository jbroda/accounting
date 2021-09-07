from django.db import models
from accounting.models import Owner
from django.contrib.auth.models import AbstractUser
from localflavor.us.models import PhoneNumberField
from hiddenpond.mixins import ChangeHistoryMixin

#########################################################################################
class MyUser(ChangeHistoryMixin, AbstractUser):
    phone_number = PhoneNumberField(blank=True)
    owner = models.OneToOneField(Owner,null=True,blank=True)
