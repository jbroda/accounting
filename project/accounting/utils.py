from django.utils import timezone
from django.contrib.auth.models import User
from elasticsearch.exceptions import ConnectionError
from .models import Account, Entry
import sys
import logging
import datetime

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
def add_transaction_entry(user, accounts, category, 
                          amount=None, memo=None, date=None,
                          timestamp=None):
    try:
        response = ""

        now = timezone.now()

        entry_date = now

        if date:
            if type(date) is datetime.date:
                logger.info("date is {0}".format(date))

                if timestamp:
                    # Combine the passed-in date with the given timestamp.
                    entry_date = datetime.datetime.combine(date, timestamp.time())
                    entry_date = datetime.datetime.combine(entry_date, timestamp.timetz())
                else:
                    # Combine the passed-in date with the current local time.
                    entry_date = datetime.datetime.combine(date, datetime.datetime.today().time())
                    entry_date = timezone.make_aware(entry_date, timezone.get_default_timezone())
            else:
                logger.info("datetime is {0}".format(date))
                entry_date = date

        if amount is None:
            amount = category.amount

        if memo is None:
            memo = "{0} for {1:%B} {1:%Y}".format(category.name, entry_date)

        if timestamp is None:
            timestamp = now

        for account in accounts:
            logger.info("{0}: applying {1} of ${2:.2f} for {3} with t={4} ...\n".
                        format(account.acct_id, category.name, amount, entry_date, timestamp))

            # Get the current account balance from the account's entry 
            # immediately before the current entry date.
            last_entry = Entry.objects.filter(account=account,
                                              datetime__lte=entry_date).order_by('-datetime')[:1]
            balance = last_entry[0].balance if last_entry else 0

            logger.info('ACCOUNT BALANCE {0} as of {1}'.format(balance, entry_date))

            # Create a new entry with the given parameters.
            entry = Entry(user=user, datetime=entry_date, timestamp=timestamp, amount=amount, 
                          memo=memo, category=category, account=account)

            # Set the running balance in the new entry.
            balance = balance + amount
            entry.balance = balance

            # Save the entry.
            entry.save()

            # Update the running balance in entries after the current entry date.
            entries = Entry.objects.filter(account=account,
                                           datetime__gt=entry_date).order_by('datetime')
            for entry in entries:
                balance = balance + entry.amount
                entry.balance = balance
                logger.info('entry: {0}'.format(str(entry)))
                entry.save()

            logger.info('NEW ACCOUNT BALANCE: {0}'.format(balance))

            # Set the running balance in the account object.
            entry.account.balance = balance
            try:
                entry.account.save()
            except ConnectionError, e:
                logger.exception(e)

            # Update the response string.
            response += account.acct_id + ":" + str(entry.account.balance) + ",";

            logger.info('%s: applied $%.2f %s!\n' % (account.acct_id, amount, category.name))

        return response

    except Exception, e:
            logger.exception(e)
