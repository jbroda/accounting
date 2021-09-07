from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from dateutil.relativedelta import relativedelta
from accounting.models import Account, Category, Entry
from accounting.utils import add_transaction_entry
import datetime
import logging

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = '<acct_id acct_id ...>'
    help = 'Applies the assessment to accounts ...'

    def handle(self, *args, **options):
        try:
            # Retrieve the assessment category.
            assessment = Category.objects.get(type=Category.ASSESSMENT)

            # Apply the assement at 10:00:00 am.
            now = datetime.datetime.now()
            now = now.replace(hour=10, minute=00, second=0, microsecond=0)
            now = timezone.make_aware(now, timezone.get_current_timezone())

            # Compute the date of the first of the next month.
            first_of_next_month = now + relativedelta(months=1)
            first_of_next_month = first_of_next_month.replace(day=1)

            # Check if the assessment was already applied.
            test_account = Account.objects.filter(acct_id='B9011')
            if test_account is None:
                raise Exception('Account B9011 not found!')
            test_entry = Entry.objects.filter(account=test_account,
                                              datetime=first_of_next_month,
                                              category=assessment)
            if test_entry:
                result = 'warning'
                raise Exception('The assessments for {0:%B %Y} have already been applied!'.
                                format(first_of_next_month))

            # Specify accounts to apply assessment.
            if args:
                accounts = Account.objects.filter(acct_id__in=args)
            else:
                # Apply to all accounts except for the general account.
                accounts = Account.objects.exclude(acct_id__in=settings.EXCLUDED_ACCOUNTS)
        
            # Use the sytem user to apply charges.
            user = User(username="system")

            # Charge the assessment at 10:00:00 am of the first of the month.
            add_transaction_entry(user, accounts, assessment,
                                  date=first_of_next_month,
                                  memo=assessment.name)
        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
