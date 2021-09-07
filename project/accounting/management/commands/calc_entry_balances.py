from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from accounting.models import Account, Category, Entry
from accounting.utils import add_transaction_entry
from datetime import date, datetime, tzinfo, timedelta
from dateutil import parser
import string
import re
import logging
from decimal import Decimal


###############################################################################
logger = logging.getLogger(__name__)

##############################################################################
class cst(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-6)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "CST"

###############################################################################
class Command(BaseCommand):
    args = '[<acct_id|orig_id>]'
    help = 'Calculate entry balances for the given account'

    def handle(self, *args, **options):
        try:
            accounts = []
            if len(args) > 0:
                logger.info('looking up account {0} ...'.format(args[0]))
                try:
                    account = Account.objects.get(orig_id=args[0])
                    accounts = [account]
                except ObjectDoesNotExist:
                    try:
                        account = Account.objects.get(acct_id=args[0])
                        accounts = [account]
                    except ObjectDoesNotExist:
                        pass

            if accounts:
                logger.info('found account {0}!'.format(accounts[0].acct_id))
            else:
                accounts = Account.objects.all()

            for account in accounts:
                entries = Entry.objects.filter(account=account).order_by("datetime")
                account.balance = 0 
                next_minute = 1
                logger.info("initial {0} balance: {1}".format(account.acct_id, account.balance))
                for entry in entries:
                    new_datetime = timezone.make_naive(entry.datetime,timezone=cst())
                    new_datetime = new_datetime.replace(hour=14, minute=0, second=0, 
                                                        microsecond=0, tzinfo=cst())
                    new_timestamp = new_datetime

                    if entry.category.type == Category.PAYMENT:
                        new_timestamp = new_timestamp.replace(minute=next_minute)                       
                        new_datetime = new_timestamp
                        next_minute = next_minute + 1
                    else: 
                        next_minute = 1

                    entry.datetime = new_datetime
                    entry.timestamp = new_timestamp
                    entry.balance = account.balance + entry.amount
                    account.balance = entry.balance
                    logger.info('entry: {0}'.format(str(entry)))
                    entry.save()
                
                # Save account balance.
                account.save()
                logger.info('account: {0}'.format(str(account)))

        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
