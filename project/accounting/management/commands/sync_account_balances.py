from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import timezone
from accounting.models import Account, Category, Entry
from accounting.utils import add_transaction_entry
import logging

###############################################################################
logger = logging.getLogger(__name__)

###############################################################################
class Command(BaseCommand):
    args = '[<acct_id|orig_id>]'
    help = 'Synchronizes account balances with the account entries ...'

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
                    except ObjectDoesNotExist, e:
                        self.stderr.write("ERROR: " + str(e))
                        return

            if accounts:
                logger.info('found account {0} with balance {1}!'.
                            format(accounts[0].acct_id, accounts[0].balance))
            else:
                accounts = Account.objects.all()

            if not accounts:
                raise Exception('No accounts found!')

            self.stdout.write('syncing account balances ...')

            # Iterate through all accounts
            for account in accounts:
                last = account.entry_set.order_by('datetime','balance').last()
                logger.info('last entry: {0}'.format(str(last)))
                account.balance = last.balance
                account.save()
                logger.info('new balance: {0}'.format(account.balance))
                self.stdout.write('.',ending='')

            self.stdout.write('DONE syncing account balances!')

        except Exception, e:
            logger.exception(e)
            self.stderr.write("ERROR: " + str(e))
