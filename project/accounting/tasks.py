from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from dateutil.relativedelta import relativedelta
from django.core.files.base import ContentFile
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Account, Entry, Category
from .utils import add_transaction_entry
from tempfile import NamedTemporaryFile
from time import strftime
import cStringIO
import datetime
import logging
import sys
import os
import subprocess
import zipfile
import re


##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
def backup_db():
    success = False
    try:
        # Get the current date/time.
        now = datetime.datetime.now()
        now = timezone.make_aware(now, timezone.get_default_timezone())

        # Create a time string to be used as a part of filenames.
        time_fmt = '%Y_%m_%d_%H_%M_%S'
        time_str = now.strftime(time_fmt)

        # Configure Postgres environment.
        os.putenv('PGDATABASE',settings.DATABASES['default']['NAME'])
        os.putenv('PGUSER',settings.DATABASES['default']['USER'])
        os.putenv('PGHOST',settings.DATABASES['default']['HOST'])
        os.putenv('PGPORT',settings.DATABASES['default']['PORT'])
        os.putenv('PGPASSWORD',settings.DATABASES['default']['PASSWORD'])

        # Create a named temporary file.
        tmpfile = NamedTemporaryFile(delete=False)
        dump_file = tmpfile.name
        tmpfile.close()

        # Dump the entire database to the temporary file.
        command = '{0} -f {1}'.format('pg_dump', dump_file)
        logger.info("Command: {0}".format(command))
        subprocess.call(command, shell=True)
        logger.info("dump finished")

        # Write the dump file to the ZIP buffer.
        zipbuf = cStringIO.StringIO()
        zf = zipfile.ZipFile(zipbuf, "w", zipfile.ZIP_DEFLATED, False)
        zf.write(dump_file,'hp_db_' + time_str + '.sql')
        zf.close()

        # Remove the temporary dump file.
        os.remove(dump_file)

        # Backup directory under the default storage.
        BACKUP_DIR = 'backup/'

        # Delete backups older than 12 months.
        try:
            twelve_months_ago = now - relativedelta(months=12)
            dirs, files = default_storage.listdir(BACKUP_DIR)
            for file in files:
                file = os.path.join(BACKUP_DIR, file)
                match = re.match(r".+hp_db_(?P<time>\w+).sql.zip$", file)
                if match:
                    t = match.group('time')
                    file_time = datetime.datetime.strptime(t, time_fmt)
                    file_time = timezone.make_aware(file_time, timezone.get_default_timezone())

                    if file_time < twelve_months_ago:
                        logger.info("DELETING file %s" % file)
                        default_storage.delete(file)
                        logger.info("DELETED file %s" % file)
                    else:
                        logger.info("KEEPING file %s" % file)
        except Exception, e:
            logger.exception(e)

        # Save the ZIP buffer in the backup directory.
        zip_file = BACKUP_DIR + 'hp_db_' + time_str + '.sql.zip'
        default_storage.save(zip_file, ContentFile(zipbuf.getvalue()))
        logger.info("SAVED " + zip_file)
        success = True
    except Exception, e:
        logger.exception(e)

    return success

##############################################################################
@login_required
def apply_assessments(request):
    result = 'danger'
    message = 'Failed to apply the monthly assessment!'
    try:
        # Retrieve the assessment category.
        assessment = Category.objects.get(type=Category.ASSESSMENT)

        # Apply the assement at 10:00:00 am.
        now = datetime.datetime.now()
        now = now.replace(hour=10, minute=00, second=0, microsecond=0)
        now = timezone.make_aware(now, timezone.get_current_timezone())

        # Apply the late fees between the 16th and last day of the current month.
        if now.day < 20:
            raise Exception('Please apply assessments between the 20th and last day of the month!')

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

        # Backup the database before proceeding.
        success = backup_db()
        if not success:
            raise Exception('Failed to back up the database')

        # Apply to all accounts except for the general account.
        accounts = Account.objects.exclude(acct_id__in=settings.EXCLUDED_ACCOUNTS)

        # Use the sytem user to apply charges.
        user = User(username="system")

        # Charge the assessment at 10:00:00 am of the first of the month.
        add_transaction_entry(user, accounts, assessment,
                              date=first_of_next_month,
                              memo=assessment.name)
        result = 'success'
        message = 'The assessment for {0:%B %Y} has been applied!'.format(first_of_next_month)

    except Exception, e:
        logger.exception(e)
        message = str(e)

    response = TemplateResponse(request, 
                                'accounting/task_result.html', 
                                {'title'   : 'Monthly Assessments',
                                 'result'  : result,
                                 'message' : message})
    return response


##############################################################################
@login_required
def apply_late_fees(request):
    result = 'danger'
    message = 'Failed to apply the late fees!'
    late_accounts = ()

    try:
        # Retrieve the assessment category.
        assessment = Category.objects.get(type=Category.ASSESSMENT)

        # Retrieve the late fee category.
        late_fee = Category.objects.get(name=Category.LATE_FEE)

        # Apply the late fees between the 16th and last day of the current month.
        now = datetime.datetime.now()
        now = timezone.make_aware(now, timezone.get_current_timezone())
        if now.day < 16:
            raise Exception('Please apply late fees between the 16th and last day of the month!')

        # Compute the date of the first of the next month.
        first_of_next_month = now + relativedelta(months=1)
        first_of_next_month = first_of_next_month.replace(day=1)

        # Check if the late fees were already applied to any account this month.
        accounts = Account.objects.exclude(acct_id__in=settings.EXCLUDED_ACCOUNTS)
        test_entries = Entry.objects.filter(account__in=accounts,
                                            datetime__month=now.month,
                                            datetime__year=now.year, 
                                            category=late_fee)
        if test_entries:
            #for e in test_entries:
            #    logger.info("entries: {0}".format(e))
            result = 'warning'
            #late_accounts = [ entry.account for entry in test_entries ]
            #late_accounts = sorted(late_accounts, key=lambda a: (a.balance), reverse=True) 
            raise Exception('The late fees for {0:%B %Y} have already been applied!'.format(now))

        # Backup the database before proceeding.
        success = backup_db()
        if not success:
            raise Exception('Failed to back up the database')

        # Iterate through all accounts except for the excluded accounts (e.g. the general account).
        for account in accounts:
            acct_id = account.acct_id # Retrieve the account id

            logger.info('%s: evaluating account charges ...' % acct_id)

            # Get the last account entry up to the first of the next month.
            last_entry = account.entry_set.filter(datetime__lt=first_of_next_month).order_by('-datetime')[:1]

            # Get the outstanding balance from the last account entry 
            # before the first of the next month.
            balance = last_entry[0].balance if last_entry else account.balance
            logger.info('%s: current balance: %.2f' % (acct_id, balance))

            # Get the account charges up to the first of the next month.
            charges = account.entry_set.filter(datetime__lt=first_of_next_month,
                                               category__type__in=[Category.CHARGE, 
                                                                   Category.ASSESSMENT]).order_by('-datetime')
            assessmentDue = 0;  # Total assessment due
            otherDue = 0;       # Total other charges due

            for charge in charges:
                logger.info("charge: {0}".format(charge))
                if (balance > 0):
                    if (balance < charge.amount):
                        charge.amount = balance # This takes care of partial payments on a charge

                    balance -= charge.amount;

                    if (charge.category.type == Category.ASSESSMENT):
                        assessmentDue += charge.amount
                    elif (charge.category.type == Category.CHARGE):
                        otherDue += charge.amount
                    else:
                        raise Exception('Unexpected charge type: ' + str(charge.category.type))
                else:
                    break

            logger.info("%s: total assessment due: %.2f" % (acct_id, assessmentDue))
            logger.info("%s: total other charges due: %.2f" % (acct_id, otherDue))

            # Assess the late fee to accounts whose total assessment due is 
            # greater or equal to the monthly assessment amount.
            user = User(username="system")
            if (assessmentDue >= assessment.amount):
                # Add the late fee to the account.
                logger.info('ADDING late fee for {0}. Amount due: {1}'.format(acct_id,assessmentDue))
                add_transaction_entry(user, [account], late_fee, memo='Late Fee')

                # Add the account to the list of late accounts.
                late_accounts += (account,)

        result = 'success'
        message = 'The late fees have been applied to the late accounts.'

    except Exception, e:
        logger.exception(e)
        message = str(e)

    response = TemplateResponse(request, 
                                'accounting/task_result.html', 
                                {'title'    : 'Late Fees',
                                 'result'   : result,
                                 'message'  : message,
                                 'accounts' : late_accounts})
    return response

