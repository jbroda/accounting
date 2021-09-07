from django.apps import AppConfig
from django.contrib import admin
import logging
from .signals import register_signals

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class HPConfig(AppConfig):
    name = 'hiddenpond'
    verbose_name = 'Hidden Pond'
    def ready(self):
        register_signals()