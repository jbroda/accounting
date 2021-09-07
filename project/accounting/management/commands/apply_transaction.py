from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from accounting.models import Account, Category, Entry
from accounting.utils import add_transaction_entry
from dateutil import parser
import datetime
import string
import re
import logging
from decimal import Decimal

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = '<acct_id|orig_id> <date> <memo> <category> <amount> <balance> [<timestamp>]'
    help = 'Applies the given transaction'

    def handle(self, *args, **options):
        try:
            logger.info('looking up account {0} ...'.format(args[0]))
            try:
                account = Account.objects.get(orig_id=args[0])
            except ObjectDoesNotExist:
                account = Account.objects.get(acct_id=args[0])

            logger.info('found account {0}!'.format(args[0]))


            logger.info('DATE: {0}'.format(args[1]))
            """
            try:
                [month,day,year] = [int(n) for n in string.split(args[1],'/')]
            except ValueError:
                [year,month,day] = [int(n) for n in string.split(args[1],'-')]
            date = datetime.datetime(year, month, day, 14, 0, 0, 0, timezone.get_current_timezone())
            """
            date = parser.parse(args[1])
            date = date.replace(hour=14,tzinfo=timezone.get_current_timezone())
            memo = string.capwords(str(args[2]))
            cat = str(args[3]).lower()
            amount = Decimal(args[4])
            balance = Decimal(args[5]) if args[5] else None
            timestamp = None
            try:
                if len(args) > 6:
                    timestamp = parser.parse(args[6])
            except Exception,e:
                logger.exception(e)

            if memo == "F/c":
                memo = "Finance Charge"

            cat_name = ""
            cat_type = Category.CHARGE
            if re.match("assessment", cat) or re.match("assesment", cat):
                cat_type = Category.ASSESSMENT
            elif re.match("credit", cat):
                cat_type = Category.PAYMENT
            elif re.match("finance charge", cat):
                cat_name = Category.LATE_FEE
            elif re.match("other charge", cat):
                if re.search("lease", memo, re.IGNORECASE):
                    cat_name = Category.LEASE_FINE
                elif re.search("pool", memo, re.IGNORECASE):
                    cat_name = Category.POOL_DOOR_KEY_FEE
                elif re.search("tennis", memo, re.IGNORECASE):
                    cat_name = Category.TENNIS_COURT_KEY_FEE
                elif re.search("entry", memo, re.IGNORECASE):
                    cat_name = Category.ENTRY_DOOR_FEE
                elif re.search("returned", memo, re.IGNORECASE):
                    cat_name = Category.RETURNED_CHECK_FEE
                elif re.search("legal", memo, re.IGNORECASE):
                    cat_name = Category.LEGAL_FEE
                elif re.search("legalfees", memo, re.IGNORECASE):
                    cat_name = Category.LEGAL_FEE
                elif re.search("repair", memo, re.IGNORECASE):
                    cat_name = Category.REPAIR_FEE
                elif re.search("fine", memo, re.IGNORECASE):
                    cat_name = Category.MISC_FINE
                else:
                    cat_name = Category.MISC_FEE
            else:
                raise Exception("No such category: " + cat)

            if cat_name:
                #print "CATEGORY NAME: ", cat_name
                category = Category.objects.get(name=cat_name)
            else:
                #print "CATEGORY TYPE: ", cat_type
                category = Category.objects.get(type=cat_type)

            logger.info("account: {0}, date: {1}, memo: {2}, cat: {3}, amount: {4}, balance: {5}, timestamp: {6}"
                        .format(account.acct_id, date, memo, category.name, amount, balance, timestamp))

            user = User(username="system")
            add_transaction_entry(user, [account], category, amount, memo, date, timestamp)
                
        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
