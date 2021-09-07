from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from accounting.models import Account, Category, Entry
from datetime import date, datetime, tzinfo, timedelta
from dateutil import parser
import string
import re
import logging
from decimal import Decimal


###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = '<entry_id>'
    help = 'Delete the given entry'

    def handle(self, *args, **options):
        try:
            entry_id = args[0]

            e = Entry.objects.get(pk=entry_id)

            logger.info('Deleting ENTRY: {0}'.format(str(e)))

            e.delete()

        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
