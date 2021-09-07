from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from accounting.models import Account, Category, Entry
from accounting.utils import add_transaction_entry
import logging

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = '<acct_id acct_id ...>'
    help = 'Applies the late fee to all accounts ...'

    def handle(self, *args, **options):
        try:
            # Retrieve the assessment category.
            assessment = Category.objects.get(type=Category.ASSESSMENT)

            # Retrieve the late fee category.
            late_fee = Category.objects.get(name=Category.LATE_FEE)

            if args:
                accounts = Account.objects.filter(acct_id__in=args)
            else:
                accounts = Account.objects.all()

            if not accounts:
                raise Exception('No accounts found!')

            # Iterate through all accounts
            for account in accounts:

                acct_id = account.acct_id # Retrieve the account id

                #logger.info('%s: evaluating account charges ...' % acct_id)

                balance = account.balance          # outstanding balance
                #logger.info('%s: current balance: %.2f' % (acct_id, balance))

                charges = account.entry_set.filter(category__type__in=[Category.CHARGE, Category.ASSESSMENT]).order_by('-datetime')

                assessmentDue = 0;  # total assessment due
                otherDue = 0;       # total other charges due

                for charge in charges:
                    if (balance > 0):
                        if (balance < charge.amount):
                            charge.amount = balance # this takes care of partial payments on a charge

                        balance -= charge.amount;

                        if (charge.category.type == Category.ASSESSMENT):
                            assessmentDue += charge.amount
                        elif (charge.category.type == Category.CHARGE):
                            otherDue += charge.amount
                        else:
                            raise Exception('Unexpected charge type: ' + str(charge.category.type))
                    else:
                        break

                #logger.info("%s: total assessment due: %.2f" % (acct_id, assessmentDue))
                #logger.info("%s: total other charges due: %.2f" % (acct_id, otherDue))

                # Assess the late fee
                user = User(username="system")
                if (assessmentDue >= assessment.amount):
                    #logger.info('Assessment due {0} is gte than {1}'.format(assessmentDue, assessment.amount))
                    logger.info('ADDING late fee for {0}. Amount due: {1}'.format(acct_id,assessmentDue))
                    add_transaction_entry(user, [account], late_fee, memo='Late Fee')

        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
