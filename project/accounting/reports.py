from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.core import serializers
from django.http import HttpResponse 
from django.views.generic import TemplateView
from django.utils import timezone
from django.shortcuts import render
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.base import ContentFile
from django.template.response import TemplateResponse
from django.core import mail
from django.core.mail import EmailMessage
from braces.views import StaffuserRequiredMixin
from xhtml2pdf import pisa
from PyPDF2 import PdfFileWriter, PdfFileReader
from itertools import chain
from datetime import timedelta
from .models import Account, Owner, Entry, Category, Lease, Tenant, Vehicle
from .forms import AccountEntryForm, AccountForm, OwnerForm
from .myrequests import spawn_request, update_request, cancel_request
import cStringIO
import io
import logging
import sys
import json
import time
import datetime
import os
import zipfile
import shutil
import multiprocessing
from decimal import Decimal
import string
from .list_file import *

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
def fetch_resources(uri, rel):
    """ Access files and images."""
    path = os.path.join(staticfiles_storage.location, 
                        uri.replace(staticfiles_storage.base_url, ""))
    return path

##############################################################################
class DelinquentInfoItem:
    def __init__(self):
        self.account = None
        self.ownerName = None
        self.lastPaidDate = None
        self.lastPaidAmount = 0
        self.entries = None

    def __unicode__(self):
        return '%s' % (self.ownerName)

##############################################################################
def create_delinquency_report(date):
    logger.info("IN create_delinquency_report")
    start_time = time.time() * 1000;
    accounts = Account.objects.exclude(acct_id__in=settings.EXCLUDED_ACCOUNTS)
    accts = [] 
    total = 0;
    other_amt = 0;
    for x in accounts :
        bal = x.read_balance(date)
        if bal > settings.DELINQUENT_BALANCE:
            x.balance = bal
            accts.append(x)
        else:
            other_amt += bal
        total += bal;

    accts.sort(key=lambda x: x.balance, reverse=True)

    di = []
    entry = None;
    pk = 0;
    for x in accts :
        d = DelinquentInfoItem();
        ownerNames = Owner.objects.filter(account=x);
        d.ownerName = "/".join(map(str, list(ownerNames)))
        d.account = x
        last_paid_entry = Entry.objects.filter( \
            account=x,amount__lt=0,datetime__lte=date).order_by("-datetime")[:1]
        if len(last_paid_entry) > 0:
            d.lastPaidDate = last_paid_entry[0].datetime
            d.lastPaidAmount = -last_paid_entry[0].amount
        entry = Entry.objects.filter(account=x,balance__lte=0).order_by("-datetime")[:1]
     
        if len(entry) > 0: 
            d.entries = Entry.objects.filter(account=x,
                datetime__gte=entry[0].datetime, datetime__lte=date).order_by("datetime")
        else:
            d.entries = Entry.objects.filter( \
                account=x,datetime__lte=date).order_by("datetime")

        di.append(d)

    context_dict = {
        'delinquent_info': di,
        'other_amount': other_amt,
        'total_amount':total,
        'report_date' : date.strftime("%B %d, %Y")
    }

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    template_name = "accounting/pdf_account_report.html"
    template = get_template(template_name)
    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close()

    return pdf

##############################################################################
def create_transaction_report(reportType, bDate, eDate, reportRange):
    logger.info('type: {0}, bDate: {1}, eDate: {2}'.format(reportType, bDate, eDate))

    start_time = time.time() * 1000;

    totalCredits = 0.0
    totalCharges = 0.0
    type = 'All'

    if reportType == "0" :
        # Credits.
        type = 'Credit'
        entries = Entry.objects.filter(timestamp__gte=bDate,
                                       timestamp__lte=eDate,
                                       amount__lte=0).order_by("timestamp")
    elif reportType == "1":
        # Charges.
        type = 'Charge'
        entries = Entry.objects.filter(timestamp__gte=bDate,
                                       timestamp__lte=eDate,
                                       amount__gte=0).order_by("timestamp")
    else:
        # All transactions.
        type = 'All'
        entries = Entry.objects.filter(timestamp__gte=bDate,
                                       timestamp__lte=eDate).order_by("timestamp")
    for entry in entries:
        if entry.amount >= 0.0:
            totalCharges += float(entry.amount)
        else:
            totalCredits += float(entry.amount)

    context_dict = {
        'entries': entries,
        'report_range' : reportRange,
        'report_type' : type,
        'total_credits' : totalCredits,
        'total_charges' : totalCharges
    }

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    template_name = "accounting/pdf_transaction_report.html"
    template = get_template(template_name)
    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close()

    return pdf

################################################################################
class StatementInfoItem:
    def __init__(self):
        self.account = None;
        self.address = [];
        self.entries = None;

    def __unicode__(self):
        return '%s' % (self.account)

##############################################################################
def getMailingName(acct):
    ownerNames = Owner.objects.filter(account=acct);
    mailing_name = ""

    for y in ownerNames:
        if len(mailing_name) != 0:
            mailing_name += " / "
        mailing_name += y.first_name + " " + y.last_name

    return mailing_name

##############################################################################
def getMailingAddress(acct):
    ownerNames = Owner.objects.filter(account=acct);
    result = []

    mailing_name = getMailingName(acct);
    result.append(mailing_name)
            
    for y in ownerNames:
        if len(y.address) > 0:
            result.append(y.address)
            result.append(y.city + " " + y.state + ", " + y.zip)
            break;

    unit = acct.unit
    idx = unit.find("-0")
    if idx > 0: unit = unit[idx+2:]
    unit_address = acct.unit_address + " UNIT " + unit

    if y.address[:4] != unit_address[:4] :
       result.insert(1, "PROP: " + unit_address)

    return result;

##############################################################################
def is_statement_needed(account, date):
    # Skip accounts for which the 'is_no_statement' flag is true.
    if account.is_no_statement:
        logger.info("{0} skipping statement (no statement)".format(account.acct_id))
        return False

    # Check if a late fee was assessed within the last 2 weeks.
    two_weeks_ago = timezone.now() - timedelta(days=14)
    late_fees = account.entry_set.filter(category__name__in=[Category.LATE_FEE],
                                         datetime__gte=two_weeks_ago)
    is_late_fee_in_last_two_weeks = len(late_fees) > 0

    # Read the current account balance.
    bal = account.read_balance(date)

    # Statement is needed:
    # if balance is greather than the monthly assessment amount
    # or a late fee was assessed within the last 2 weeks and balance is positive
    # or balance is not a multiple of the monthly assessment amount.
    if (bal > settings.ASSESSMENT or 
        is_late_fee_in_last_two_weeks or 
        ((bal % int(settings.ASSESSMENT)) != 0)):
        return True

    return False

##############################################################################
def create_statement_report(reqId, date, acct, type, is_store_files=True):
    logger.info('date: {0}, account: {1}, type: {2}, is_store_files: {3}'.
                format(date, acct, type, is_store_files))

    try:
        start_time = time.time() * 1000
        accts = [] 
        files_or_streams = []
        final_result = cStringIO.StringIO()

        if acct == None :
            #
            # Iterate through all accounts.
            #
            accounts = Account.objects.exclude(acct_id__in=settings.EXCLUDED_ACCOUNTS)

            for x in accounts :
                # Check conditions for inclusion in the statement report.
                if is_statement_needed(x, date):
                    if x.is_email_statement:
                        logger.info("{0} skipping statement (email only)".format(x.acct_id))
                    else: 
                        accts.append(x)
        else:
            #
            # Generate a statement for a single account.
            #
            accts.append(acct)

        accts.sort(key=lambda x: x.balance, reverse=True)

        template_name = "accounting/pdf_statement_report.html"
        template = get_template(template_name)

        if is_store_files:
            tmp_output_dir_format = '{:' + settings.REPORT_DIR + '/statement/tmp_%Y_%m_%d_%H_%M_%S/}'
            tmp_output_dir = tmp_output_dir_format.format(datetime.datetime.now())
            logger.info("TMP OUTPUT DIR: %s" % tmp_output_dir)

            # Update the request with items to be deleted if cancelled.
            update_request(reqId, (tmp_output_dir,))

        for x in accts :
            s = StatementInfoItem();
            s.address = getMailingAddress(x);
            s.account = x

            if acct == None or type == 'simple':
                # Retrieve the first transaction since the last zero balance.
                entry = Entry.objects.filter( \
                   account=x, balance=0).order_by("-datetime")[:1]
            else:
                entry = [] 

            if len(entry) > 0: 
                startdate = entry[0].datetime
                startdate -= timedelta(days=60)
            else:
                if type == 'reo':
                    startdate = date
                else:
                    startdate = timezone.make_aware(datetime.datetime(1900,1,1),
                                                    timezone.get_default_timezone())

            # Retrieve transactions since the 'startdate'
            s.entries = Entry.objects.filter(account=x,
                                             datetime__gte=startdate).order_by("datetime")

            if type == 'reo' and len(s.entries) > 0:
                # Get the balance on the starting date.
                first_entry = s.entries.first()
                balance = first_entry.balance - first_entry.amount

                # Get the charges since the start date.
                charges = s.entries.filter(amount__gt=0)

                # Get the deposits since the start date.
                deposits = s.entries.filter(amount__lte=0)

                # Credits are deposits
                credits = deposits

                # Go through deposits and subtract them from the balance on the start date 
                # until you either run out of deposits to subtract or the balance becomes negative.
                if balance > 0:
                    for deposit in deposits:
                        balance += deposit.amount
                        if balance > 0:
                            # When a deposit is subtracted, if the balance is still positive, 
                            # delete it from the credit list.
                            credits = credits.exclude(id=deposit.id)
                        else:
                            # If the balance becomes negative, 
                            # don't delete the credit from the credit list 
                            # but reduce it so the beginning balance will become 0. 
                            # This is a partial credit that will remain in the transaction history.
                            for i in range(0, len(credits)):
                                if (credits[i].id == deposit.id):
                                    credits[i].amount = balance
                                    break
                            break

                # Merge the remaining credits if any and charge lists, sort by date. 
                # These are the transactions you will send for rendering.
                s.entries = sorted(chain(credits, charges), key=lambda o: o.datetime)

                # Calculate a 0 based balance on all the transactions that you have in your list 
                # you are about to send for rendering.
                balance = 0
                for entry in s.entries:
                    entry.balance = balance + entry.amount
                    balance = entry.balance

                # If you run out of deposit to subtract and you still have a balance on start date, 
                # this will become bad debt to association
                s.account.balance = balance

            report_date = date
            if type == 'reo':
                report_date = datetime.datetime.now()

            context_dict = {
                'si' : s,
                'report_date' : report_date.strftime("%B %d, %Y")
            }

            context = Context(context_dict)
            html = template.render(context)   
            result = cStringIO.StringIO()

            pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
                           link_callback=fetch_resources)

            if is_store_files:
                # Store the account PDF stream into its own file.
                account_pdf = result.getvalue()
                filename = tmp_output_dir + x.acct_id + ".pdf"
                cf = ContentFile(account_pdf)
                stored_file = default_storage.save(filename, cf)
                logger.info("stored file: %s" % stored_file)
                files_or_streams.append(stored_file)
            else:
                # Store the account PDF stream.
                files_or_streams.append(result)
                logger.info('stored PDF stream for {0}'.format(x.acct_id))

        #
        # Combine each account's PDF stream into one PDF.
        #
        if files_or_streams:
            output = PdfFileWriter()
            for f in files_or_streams:
                if is_store_files:
                    fobj = default_storage.open(f, mode="rb")
                    stream = cStringIO.StringIO(fobj.read())
                    fobj.close()
                else:
                    stream = f
                input = PdfFileReader(stream)
                count = input.getNumPages()
                for i in range(0, count) :
                    output.addPage(input.getPage(i))

                # When generating a statement report, make the number of pages even 
                # for easy double-sided printing.
                if acct is None:
                    if count % 2:
                        output.addBlankPage()

            output.write(final_result)
        else:
            logger.info("No accounts with outstanding balance")
            pisa.CreatePDF("No accounts found!", final_result, encoding='UTF-8',
                           link_callback=fetch_resources)

        # Return the PDF stream.
        pdf = final_result.getvalue()

        if is_store_files:
            # Remove the temporary output directory.
            try:
                dirs, files = default_storage.listdir(tmp_output_dir)
                for f in files:
                    f = os.path.join(tmp_output_dir, f)
                    logger.info("DELETING file %s" % f)
                    default_storage.delete(f)
                    logger.info("DELETED file %s" % f)
            except Exception, e:
                logger.exception(e)

            try:
                tmp_dir = default_storage.location + "/" + tmp_output_dir
                if os.path.exists(tmp_dir):
                    logger.info("RMDIR-ing tmp dir: %s" % tmp_dir)
                    os.rmdir(tmp_dir)
                    logger.info("RMDIR-ed tmp dir: %s" % tmp_dir)

                if default_storage.exists(tmp_output_dir):
                    logger.info("DELETE-ing tmp dir: %s" % tmp_output_dir)
                    default_storage.delete(tmp_output_dir)
                    logger.info("DELETE-ed tmp dir: %s" % tmp_output_dir)
            except Exception, e:
                logger.exception(e)

        # Compute elapsed time.
        elapsed_time = (1000 * time.time()) - start_time
        logger.info("Elapsed Time %d msec" % elapsed_time)

    except Exception, e:
        logger.exception(e)

    return pdf

################################################################################
class IncomeItemDetail:
    def __init__(self, t, a, id, d, n, m):
        self.type = t
        self.amount = a
        self.date = d
        self.acctID = id
        self.name = n
        self.memo = m

    def __unicode__(self):
       return '%s %.2f %s %s %s %s' % (self.type, self.amount, \
           self.date, self.acctID, self.name, self.memo)

##############################################################################
def create_income_report(reportType, bDate, eDate, reportRange):
    logger.info('bDate: {0}, eDate: {1}'.format(bDate, eDate))

    if reportType == '0' :
        return create_cash_income_report(bDate, eDate, reportRange)
    else:
        return create_accrual_income_report(bDate,eDate, reportRange)

###############################################################################
def create_cash_income_report(bDate, eDate, reportRange):
    try:
        start_time = time.time() * 1000

        assessment = 0
        late_fees = 0
        fines = 0
        keys = 0
        billback = 0
        misc = 0
        laundry = 0
        overpayments = 0
        xCreditTotal = 0;
        xCredits = []

        total = 0
        checksum = 0
        detail = []

        # take credits entered in period in question
        credits = Entry.objects.filter(timestamp__gte=bDate,
                            timestamp__lte=eDate, amount__lt=0)

        for e in credits :
            total = total + -e.amount

        accounts = Account.objects.all()
       
        for a in accounts :
            credit_before  = 0
            credit_current = 0
            credits = Entry.objects.filter(account=a,amount__lt=0).order_by("timestamp")

            for e in credits :
                if e.timestamp < bDate :
                    credit_before += -e.amount
                elif e.timestamp > eDate :
                    break
                else :
                    credit_current += -e.amount
                    checksum += -e.amount
                    if e.memo.startswith("X-") :
                        xCreditTotal += e.amount
                        xCredits.append(e)

            if a.acct_id == settings.GENERAL_ACCOUNT :
                if credit_current > 0 :
                    for e in credits :
                        if e.timestamp > eDate :
                            break
                        elif e.timestamp >= bDate:
                            date = '{0:%m}/{0:%d}/{0:%Y}'.format(e.datetime) 

                            if e.memo.lower().find("laundry") != -1:
                                category = "LAUNDRY"
                                laundry += -e.amount
                            else:
                                category = "MISC"
                                misc += -e.amount

                            d = IncomeItemDetail(category,-e.amount,e.account.acct_id,date, \
                                getMailingName(e.account), e.memo);
                            detail.append(d)

            elif credit_current > 0:
                charges = Entry.objects.filter(account=a, amount__gt=0, \
                        datetime__lte=eDate).order_by("timestamp")
                for c in charges :
                    orig_amount = c.amount;
                    amount = c.amount;

                    if amount <= credit_before :
                        credit_before -= amount
                    else :
                        if credit_before > 0 :
                            amount -= credit_before
                            credit_before = 0;

                        if credit_current < amount :
                            amount = credit_current

                        date = '{0:%m}/{0:%d}/{0:%Y}'.format(c.datetime)
                        if c.category.type == Category.ASSESSMENT :
                            assessment += amount
                            d = IncomeItemDetail("ASSESSMENT",amount,c.account.acct_id,date, \
                                getMailingName(c.account), "");
                            detail.append(d)
                        elif c.category.name == Category.LATE_FEE :
                            late_fees += amount
                            d = IncomeItemDetail("LATE FEE",amount,c.account.acct_id,date, \
                                getMailingName(c.account), c.memo);
                            detail.append(d)
                        elif string.find(c.category.name.lower(), "key") != -1 or string.find(c.memo.lower(), "key") != -1 :
                            keys += amount
                            d = IncomeItemDetail("KEY",amount,c.account.acct_id,date, \
                                getMailingName(c.account), c.memo);
                            detail.append(d)
                        elif c.category.name == Category.LEGAL_FEE or c.category.name == Category.MISC_FEE or \
                            c.category.name == Category.REPAIR_FEE:
                            if string.find(c.memo.lower(), "refund") != -1:
                                misc += amount
                                d = IncomeItemDetail("MISC",amount,c.account.acct_id,date, \
                                    getMailingName(c.account), c.memo);
                                detail.append(d)
                            else:
                                billback += amount
                                d = IncomeItemDetail("BILLBACK",amount,c.account.acct_id,date, \
                                    getMailingName(c.account), c.memo);
                                detail.append(d)
                        elif c.category.name == Category.LEASE_FINE or c.category.name == Category.MISC_FINE :
                            fines += amount
                            d = IncomeItemDetail("FINE",amount,c.account.acct_id,date, \
                                getMailingName(c.account), c.memo);
                            detail.append(d)
                        elif c.category.name == Category.RETURNED_CHECK_FEE :
                            misc += amount
                            d = IncomeItemDetail("MISC",amount,c.account.acct_id,date, \
                                getMailingName(c.account), c.memo);
                            detail.append(d)              
                        else :
                            d = IncomeItemDetail("ERROR %s" % str(c.category),amount,c.account.acct_id,date, \
                                getMailingName(c.account), "%s [%.2f]" % (c.memo, orig_amount));
                            detail.append(d)

                        credit_current -= amount

                    if credit_current <= 0 :
                        break;

                if credit_current > 0 :
                    overpayments += credit_current
                    d = IncomeItemDetail("OVERPAYMENT",credit_current,a.acct_id,"", \
                                getMailingName(a), "");
                    detail.append(d)
     
        logger.debug("total %f, checksum %f", total, checksum)

        checksum2 = assessment + late_fees + fines + billback \
            + misc + overpayments + keys + laundry

        context_dict = {
            'report_range' : reportRange,
            'assessment' : assessment,
            'late_fees': late_fees,
            'fines' : fines,
            'keys': keys,
            'billback' : billback,
            'misc': misc,
            'laundry': laundry,
            'overpayments': overpayments,
            'total': total,
            'total_less_x_credits': total + xCreditTotal,
            'checksum' : checksum2,
            'detail' : detail,
            'x_credit_total' : xCreditTotal,
            'x_credits' : xCredits,
            'report_type' : "Cash"
        }

        elapsed_time = (time.time() * 1000) - start_time
        logger.info("Elapsed Time %d" % elapsed_time)

        template_name = "accounting/pdf_income_report.html"
        template = get_template(template_name)
        context = Context(context_dict)
        html = template.render(context)   
        result = cStringIO.StringIO()

        pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
            link_callback=fetch_resources)
        pdf = result.getvalue()
        result.close()
    except Exception, e:
        logger.exception(e)

    return pdf

###########################################################################
def create_accrual_income_report(bDate, eDate, reportRange):
    try:
        start_time = time.time() * 1000

        assessment = 0
        late_fees = 0
        fines = 0
        keys = 0
        billback = 0
        misc = 0
        laundry = 0
        overpayments = 0

        total = 0
        detail = []

        charges = Entry.objects.filter(datetime__gte=bDate,  datetime__lte=eDate, 
            amount__gt=0)

        for c in charges : 
            amount = c.amount;

            total = total + amount
            date = '{0:%m}/{0:%d}/{0:%Y}'.format(c.datetime)
            if c.category.type == Category.ASSESSMENT :
                assessment += amount
                d = IncomeItemDetail("ASSESSMENT",amount,c.account.acct_id,date, \
                    getMailingName(c.account), "");
                detail.append(d)
            elif c.category.name == Category.LATE_FEE :
                late_fees += amount
                d = IncomeItemDetail("LATE FEE",amount,c.account.acct_id,date, \
                    getMailingName(c.account), c.memo);
                detail.append(d)
            elif string.find(c.category.name.lower(), "key") != -1 or string.find(c.memo.lower(), "key") != -1 :
                keys += amount
                d = IncomeItemDetail("KEY",amount,c.account.acct_id,date, \
                    getMailingName(c.account), c.memo);
                detail.append(d)
            elif c.category.name == Category.LEGAL_FEE or c.category.name == Category.MISC_FEE or \
                c.category.name == Category.REPAIR_FEE:
                if string.find(c.memo.lower(), "refund") != -1:
                    misc += amount
                    d = IncomeItemDetail("MISC",amount,c.account.acct_id,date, \
                        getMailingName(c.account), c.memo);
                    detail.append(d)
                else:
                    billback += amount
                    d = IncomeItemDetail("BILLBACK",amount,c.account.acct_id,date, \
                        getMailingName(c.account), c.memo);
                    detail.append(d)
            elif c.category.name == Category.LEASE_FINE or c.category.name == Category.MISC_FINE :
                fines += amount
                d = IncomeItemDetail("FINE",amount,c.account.acct_id,date, \
                    getMailingName(c.account), c.memo);
                detail.append(d)
            elif c.category.name == Category.RETURNED_CHECK_FEE :
                misc += amount
                d = IncomeItemDetail("MISC",amount,c.account.acct_id,date, \
                    getMailingName(c.account), c.memo);
                detail.append(d)   
            else :
                d = IncomeItemDetail("ERROR %s" % str(c.category),amount,c.account.acct_id,date, \
                    getMailingName(c.account), "%s [%.2f]" % (c.memo, c.amount));
                detail.append(d)

        charges = Entry.objects.filter(datetime__gte=bDate,
            datetime__lte=eDate,account__acct_id=settings.GENERAL_ACCOUNT, amount__lt=0).order_by("datetime")
        for c in charges : 
            amount = -c.amount;
            total += amount

            if c.memo.lower().find("laundry") != -1:
                category = "LAUNDRY"
                laundry += amount
            else:
                category = "MISC"
                misc += amount

            date = '{0:%m}/{0:%d}/{0:%Y}'.format(c.datetime) 
            d = IncomeItemDetail(category,amount,c.account.acct_id,date, \
                getMailingName(c.account), c.memo);
            detail.append(d)

        checksum2 = assessment + late_fees + fines + billback \
            + misc + overpayments + keys + laundry

        context_dict = {
            'report_range' : reportRange,
            'assessment' : assessment,
            'late_fees': late_fees,
            'fines' : fines,
            'keys': keys,
            'billback' : billback,
            'misc': misc,
            'laundry': laundry,
            'overpayments': overpayments,
            'total': total,
            'checksum' : checksum2,
            'detail' : detail,
            'report_type' : "Accrual"
        }

        elapsed_time = (time.time() * 1000) - start_time
        logger.info("Elapsed Time %d" % elapsed_time)

        template_name = "accounting/pdf_income_report.html"
        template = get_template(template_name)
        context = Context(context_dict)
        html = template.render(context)   
        result = cStringIO.StringIO()

        pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
            link_callback=fetch_resources)
        pdf = result.getvalue()
        result.close()
    except Exception, e:
        logger.exception(e)

    return pdf

#########################################################################
def create_account_trail_report(date):
    logger.info("IN create_account_trail_report")

    start_time = time.time() * 1000;
    accts = [] 
    accounts = Account.objects.exclude(acct_id__in=[settings.GENERAL_ACCOUNT])
    total_delinquent = 0;
    total_credit = 0;

    for x in accounts :
        bal = x.read_balance(date)
        x.balance = bal
        accts.append(x)
        if bal > 0: 
            total_delinquent += bal
        else: 
            total_credit += bal

    accts.sort(key=lambda x: x.orig_id)

    template_name = "accounting/pdf_account_trail_report.html"
    template = get_template(template_name)

    context_dict = {
        'accounts' : accts,
        'report_date' : date.strftime("%B %d, %Y"),
        'delinquency_total' : total_delinquent,
        'overpayment_total' : total_credit
    }

    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close();

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    return pdf

################################################################################
class AuditAccountItem:
    def __init__(self):
        self.account = None
        self.startBalance = 0
        self.endBalance = 0
        self.chargeTotal = 0
        self.creditTotal = 0
        self.checksum = 0
        self.pseudoEntries = []

    def __unicode__(self):
        return '%s' % (self.account)

#########################################################################
def create_account_audit_report(bDate, eDate):
    logger.info("IN create_account_audit_report")
    start_time = time.time() * 1000;
    accts = [] 
    entries = []
    accounts = Account.objects.exclude(acct_id__in=[settings.GENERAL_ACCOUNT])
    chargeTotal = 0
    creditTotal = 0
    initialDelinquency = 0
    endingDelinquency = 0
    initialOverpayment = 0
    endingOverpayment = 0
    generalAccountAdjustment = 0
    generalAccountEntries = []
    xCredits = 0

    for x in accounts :
        auditItem = AuditAccountItem()
        auditItem.account = x
        
        auditItem.startBalance = x.read_balance(bDate);
        if auditItem.startBalance > 0:
            initialDelinquency += auditItem.startBalance
        else:
            initialOverpayment += auditItem.startBalance


        auditItem.endBalance = x.read_balance(eDate);
        if auditItem.endBalance > 0:
            endingDelinquency += auditItem.endBalance
        else:
            endingOverpayment += auditItem.endBalance

        entries = Entry.objects.filter( \
            account=x,datetime__lte=eDate,datetime__gte=bDate).order_by("-datetime")

        for e in entries :
            if (e.amount > 0):
                auditItem.chargeTotal += e.amount
                chargeTotal += e.amount;
            else:
                auditItem.creditTotal += e.amount
                creditTotal += e.amount
            
            if e.memo.startswith("X-") :
                logger.info(e.memo)
                auditItem.pseudoEntries.append(e)
                if (e.amount < 0) :
                    xCredits += -e.amount

        auditItem.pseudoEntries.sort(key=lambda x: x.datetime)

        auditItem.checksum = auditItem.startBalance + auditItem.chargeTotal + \
                auditItem.creditTotal - auditItem.endBalance

        accts.append(auditItem)

    accts.sort(key=lambda x: x.account.orig_id)

    logger.info("All charges: " + str(chargeTotal) + ", All credits: " + str(creditTotal));

    # handle general account
    acct = Account.objects.get(acct_id=settings.GENERAL_ACCOUNT)
    entries = Entry.objects.filter( \
        account=acct,datetime__lte=eDate,datetime__gte=bDate).order_by("-datetime")
    for e in entries :
        if e.amount < 0:
            e.amount = -e.amount
            generalAccountAdjustment += e.amount
            generalAccountEntries.append(e)

    generalAccountEntries.sort(key=lambda x: x.datetime)

    cash_audit_entries = Entry.objects.filter( \
        amount__lt=0,datetime__lte=eDate,datetime__gte=bDate).order_by("timestamp")

    auditCredit = 0
    for e in cash_audit_entries:
        auditCredit += e.amount


    template_name = "accounting/pdf_account_audit_report.html"
    template = get_template(template_name)

    context_dict = {
        'accounts' : accts,
        'report_start_date' : bDate.strftime("%m/%d/%Y"),
        'report_end_date' : eDate.strftime("%m/%d/%Y"),
        'charges_total' : chargeTotal,
        'credit_total' : creditTotal,
        'initial_delinquency' : initialDelinquency,
        'ending_delinquency' : endingDelinquency,
        'initial_overpayment' : initialOverpayment,
        'ending_overpayment' : endingOverpayment,
        'waived_income' : xCredits,
        'general_account_adjustment' : generalAccountAdjustment,
        'general_account_entries' : generalAccountEntries,
        'cash_audit_entries' : cash_audit_entries,
        'cash_audit_total' : auditCredit
    }

    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close();

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    return pdf


################################################################################
class ExpiredLeaseItem:
    def __init__(self):
        self.lease = None;
        self.address = [];

    def __unicode__(self):
        return '%s' % (self.lease.account)

#########################################################################
def create_expired_lease_report(date):
    logger.info("IN create_expired_lease_report")
    start_time = time.time() * 1000;

    expired_leases = Lease.objects.filter(end_date__lte=date).order_by(
        "end_date") 

    lease_items = []

    for x in expired_leases:
        item = ExpiredLeaseItem()
        item.lease = x
        item.address = getMailingAddress(x.account)
        lease_items.append(item)
       
    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    template_name = "accounting/pdf_lease_expired_report.html"
    template = get_template(template_name)

    today = datetime.datetime.now()
    context_dict = {
        'leases' : lease_items,
        'report_date' : date.strftime("%B %d, %Y"),
        'today_date': today.strftime("%B %d, %Y")
    }

    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close();

    return pdf

################################################################################
class FHALeaseItem:
    def __init__(self):
        self.ownerName = None;
        self.number_of_units = 0; 

    def __unicode__(self):
        return '%s' % (self.lease.account)

#########################################################################
def create_fha_lease_report(date):
    logger.info("IN create_fha_lease_report")

    start_time = time.time() * 1000;
    fha_items = [] 
    leases = Lease.objects.all();
    total_leased_units = 0;

    for x in leases:
      if x.end_date:
        found = 0
        name = getMailingName(x.account)
        for y in fha_items :
            if y.ownerName == name:
                found = 1
                y.number_of_units += 1
                total_leased_units += 1
                break;

        if found == 0:
            item = FHALeaseItem();
            item.ownerName = name;
            item.number_of_units = 1;
            total_leased_units += 1
            fha_items.append(item)

    fha_items.sort(key=lambda x: x.ownerName)

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    template_name = "accounting/pdf_lease_fha_report.html"
    template = get_template(template_name)

    context_dict = {
        'fha_items' : fha_items,
        'report_date' : date.strftime("%B %d, %Y"),
        'total_leased_units' : total_leased_units
    }

    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close();

    return pdf

################################################################################
class VOSLeaseItem:
    def __init__(self):
        self.ownerInfo = [];
        self.properties = []; 

    def __unicode__(self):
        return '%s' % (self.lease.account)


#########################################################################
def create_vos_lease_report(date):
    logger.info("create_vos_lease_report")

    start_time = time.time() * 1000;
    vos_items = [] 

    # Sort leases by account owner's last name.
    leases = Lease.objects.all().order_by('account__owner__last_name')

    # Keep track of accounts that were already processed.
    processed_accounts = dict()

    for x in leases:
        # Skip processed accounts.
        if processed_accounts.get(x.account.acct_id):
            continue
        else:
            processed_accounts[x.account.acct_id] = True

        # Skip leases for which tenants are relatives of the owner.
        is_tenant_owners_relative = False
        for tenant in x.tenant_set.all():
            if tenant.is_owners_relative:
                logger.info("{0}: tenant '{1}' is relative of '{2}'".
                            format(x.account.acct_id, tenant, x.account.owner_set.first()))
                is_tenant_owners_relative = True
        if is_tenant_owners_relative:
            continue

        if not x.start_date:
            logger.info("Lease for {0} is empty. Skipping.".format(x.account.acct_id))
            continue
         
        found = 0
        ownerInfo = getMailingAddress(x.account)
        for y in vos_items :
            if y.ownerInfo[0] == ownerInfo[0]:
                item = y;
                found = 1
                break;

        if found == 0:
            item = VOSLeaseItem();
            item.ownerInfo = ownerInfo;
            vos_items.append(item)

        if ownerInfo[1].startswith("PROP:"):
           item.properties.append(ownerInfo[1]);
           del ownerInfo[1];

    vos_items[:] = [x for x in vos_items if x.properties]

    elapsed_time = (time.time() * 1000) - start_time
    logger.info("Elapsed Time %d" % elapsed_time)

    template_name = "accounting/pdf_lease_vos_report.html"
    template = get_template(template_name)

    context_dict = {
        'vos_items' : vos_items,
        'report_date' : date.strftime("%B %d, %Y")
    }

    context = Context(context_dict)
    html = template.render(context)   
    result = cStringIO.StringIO()

    pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
        link_callback=fetch_resources)
    pdf = result.getvalue()
    result.close();

    return pdf

###############################################################################
def save_pdf_to_file(pdf,
                     report_name, 
                     report_type=None,
                     start_date=None,
                     end_date=None):
    logger.info("IN save_pdf_to_file")
    pdf_file_url = "/report_error/"
    pdf_file_path = "/report_error/"

    try:
        report_dir = settings.REPORT_DIR + "/" + report_name + "/"
        pdf_file_name_format = ('{:' + report_dir + report_name + 
                                (('_' + str(report_type)) if report_type else '') + 
                                '_%Y_%m_%d_%H_%M_%S.pdf}')
        pdf_file = pdf_file_name_format.format(datetime.datetime.now())

        # Save the pdf file in the default storage.
        cf = ContentFile(pdf)
        stored_file = default_storage.save(pdf_file, cf)

        # Provide the url to the stored PDF file.
        pdf_file_url = default_storage.url(stored_file)

        # Provide the absolute path to the stored PDF file.
        pdf_file_path = "/" + os.path.basename(default_storage.location) + "/" + pdf_file

        # Increment the number of files in the list file.
        update_list_file(True, report_dir)
    except Exception, e:
        logger.exception(e)

    logger.info("PDF URL: %s" % pdf_file_url)
    logger.info("PDF FILE: %s" % pdf_file_path)
    return pdf_file_url, pdf_file_path

###################################################################################
class DelinquencyReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN DelinquencyReport")
        pdf_file_url = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            reportDate = self.kwargs.get('date')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reportDate, outputQ)
            spawn_request(reqId, runDelinquencyReport, params)

            # Get the report url and path.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###################################################################################
def runDelinquencyReport(reportDate,outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        try:
            date = datetime.datetime.strptime(reportDate, "%Y-%m-%d")
            date = datetime.datetime.combine(date, datetime.datetime.today().time())
            date = timezone.make_aware(date,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            date = timezone.now()

        logger.info("STARTED report for " + str(date))
        pdf = create_delinquency_report(date)
        logger.info("FINISHED report for " + str(date))

        # Return the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf,
                                                       report_name="delinquency", 
                                                       start_date=date)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))
    except Exception, e:
        logger.exception(e)

###############################################################################
class TransactionsReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN TransactionsReport")
        pdf_file_url = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            reportType = self.kwargs.get('type')
            beginDate = self.kwargs.get('bDate')
            endDate = self.kwargs.get('eDate')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reportType, beginDate, endDate, outputQ)
            spawn_request(reqId, runTransactionReport, params)

            # Get the report url and path.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###############################################################################
def runTransactionReport(reportType, beginDate, endDate, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        now = timezone.now()

        if not reportType:
            reportType = "0";
            beginDate = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
            endDate = beginDate

        beginDate += " 00:00:00"
        endDate   += " 23:59:59"

        try:
            bDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d %H:%M:%S")
            eDate = datetime.datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S")
            bDate = timezone.make_aware(bDate,timezone.get_default_timezone())
            eDate = timezone.make_aware(eDate,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            bDate = now
            eDate = now

        reportRange = "From " + str(bDate.month) + "-" + str(bDate.day) + \
            "-" + str(bDate.year) + " to " + str(eDate.month) + "-" + \
            str(eDate.day) + "-" + str(eDate.year)

        logger.info("Report Type: %s" % str(reportType))
        logger.info("Begin Date: %s" % str(bDate))
        logger.info("End Date: %s" % str(eDate))
        logger.info("Range: %s" % reportRange)

        logger.info("STARTED report type " + str(reportType) + " for " + str(bDate) + " through " + str(eDate))
        pdf = create_transaction_report(str(reportType), bDate, eDate, reportRange)
        logger.info("FINISHED report type " + str(reportType) + " for " + str(bDate) + " through " + str(eDate))

        # Return the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf, 
                                                       report_name="transaction", 
                                                       report_type=reportType,
                                                       start_date=bDate, 
                                                       end_date=eDate)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))
    except Exception,e:
        logger.exception(e)

###################################################################################
class StatementReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN StatementReport")
        pdf_file_url = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            reportDate = self.kwargs.get('date')
            accountId = self.kwargs.get('accountId')
            reportType = self.kwargs.get('type')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reqId, reportDate, accountId, reportType, outputQ)
            spawn_request(reqId, runStatementReport, params)

            # Get the report url.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###################################################################################
def runStatementReport(reqId, reportDate, accountId, reportType, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        account_id = accountId

        logger.info("statement date: " +  str(reportDate))

        account = None
        if account_id:
            logger.info("Got account ID: %s" % account_id)
            accts = Account.objects.filter(acct_id=account_id)
            if accts.count() > 0 :
                account = accts[0]
            else :
                accts = Account.objects.filter(orig_id=account_id)
                if accts.count() > 0 :
                    account = accts[0]
        else:
            account_id = "all"

        try:
            if (reportType == 'reo'):
                # For the REO statement, use the earliest time on the given date.
                date = datetime.datetime.strptime(reportDate + " 00:00:01", "%Y-%m-%d %H:%M:%S")
            else:
                # For other statements, combine the given date with the current time.
                date = datetime.datetime.strptime(reportDate, "%Y-%m-%d")
                date = datetime.datetime.combine(date, datetime.datetime.today().time())
            date = timezone.make_aware(date,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            date = timezone.now()

        logger.info("STARTED report for " + str(date))
        pdf = create_statement_report(reqId, date, account, reportType)
        logger.info("FINISHED report for " + str(date))

        # Respond with the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf, 
                                                       report_name="statement", 
                                                       report_type=account_id,
                                                       start_date=date)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url,pdf_file_path))
    except Exception, e:
        logger.exception(e)

###################################################################################
class EMailStatements(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN EMailStatements")

        result = 'danger'
        message = 'Failed to e-mail account statements!'
        accounts = None
        account_ids = []

        try:
            # Get the current time.
            now = datetime.datetime.now()
            now = timezone.make_aware(now, timezone.get_default_timezone())

            # Close the DB connection to eliminate some database errors.
            from django.db import connection
            connection.close()

            # Extract request parameters.
            reqId = self.kwargs.get('reqId')

            # Spawn the process to e-mail account statements.
            outputQ = multiprocessing.Queue()
            outputQ.put(account_ids)
            params = (reqId, outputQ)
            spawn_request(reqId, runEmailStatements, params)

            # Get the processed accounts.
            account_ids = outputQ.get()
            accounts = Account.objects.filter(acct_id__in=account_ids)
            if accounts:
                result = 'success'
                message = 'Statements were e-mailed to the following accounts:'
            else:
                result = 'warning'
                message = 'Found no accounts to which e-mail statements!'

        except Exception, e:
            logger.exception(e)

        response = TemplateResponse(request, 
                                    'accounting/task_result.html', 
                                    {'title'    : 'Statements',
                                     'result'   : result,
                                     'message'  : message,
                                     'accounts' : accounts})
        return response

###################################################################################
def runEmailStatements(reqId, outputQ):
    logger.info('PID: %d - STARTED' % os.getpid())
    try:
        start_time = time.time() * 1000
        sent_accounts = []

        # Get the current date and time.
        now = datetime.datetime.now()
        now = timezone.make_aware(now, timezone.get_default_timezone())

        # Apply to accounts with the 'E-Mail Statement' flag set to True.
        accounts = Account.objects.filter(is_email_statement=True)

        for account in accounts:
            logger.info('Processing account {0} ...'.format(account.acct_id))

            # Send it to the first owner with an email.
            owner = None
            for o in account.owner_set.all():
                if o.email:
                    owner = o
                    break

            if owner is None:
                logger.error("No owner email found for {0}!".format(account.acct_id))
                continue

            if not is_statement_needed(account, now):
                logger.info("No statement needed for {0}!".format(account.acct_id))
                continue

            # Create the email message object.
            FROM_EMAIL  = os.getenv('SERVER_EMAIL','contact@XXXXXXXXX.XX')
            REPLY_EMAIL = os.getenv('SERVER_EMAIL','contact@XXXXXXXXX.XX')
            subject = 'Hidden Pond account statement as of {0:%B} {0:%d}, {0:%Y}'.format(now)
            body  = 'Hello {0} {1}!\n\n'.format(owner.first_name, owner.last_name)
            body += 'Please find attached the statement of account {0} as of {1:%B} {1:%d}, {1:%Y}.\n\n'.format(account.acct_id, now)
            body += '---\nHidden Pond Condominium Association\nemail: {0}\nphone: (224) 366-0060'.format(REPLY_EMAIL)
            from_email = 'Hidden Pond <{0}>'.format(FROM_EMAIL)
            reply_email = 'Hidden Pond <{0}>'.format(REPLY_EMAIL)
            to_email = [owner.email]
            bcc = [from_email,reply_email]
            email_msg = EmailMessage(subject, body, from_email, to_email, bcc, headers={'Reply-To':reply_email})

            # Create a statement for the given account
            accountId = account.acct_id
            statementDate = now
            statementType = 'simple'
            logger.info("STARTED {0} statement for {1}".format(accountId, statementDate))
            pdf = create_statement_report(reqId, statementDate, account, statementType, False)
            logger.info("FINISHED {0} statement for {1}".format(accountId, statementDate))

            # Attach the account statement to the email message.
            email_msg.attach('{0}_{1:%b}_{1:%d}_statement.pdf'.format(accountId, now), 
                             pdf, 'application/pdf')

            # Send the email.
            logger.info("Sending {0} statement to {1} ...".format(accountId, owner.email))
            connection = mail.get_connection()
            connection.open()
            connection.send_messages([email_msg])
            connection.close()
            logger.info("Sent {0} statement to {1}!".format(accountId, owner.email))

            # Keep track which accounts were emailed a statement.
            sent_accounts.append(account.acct_id)

        # Return account IDs that were emailed statements.
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put(sent_accounts)

        elapsed_time = (1000 * time.time()) - start_time
        logger.info("Elapsed Time %d msec" % elapsed_time)

    except Exception, e:
        logger.exception(e)

    logger.info('PID: %d - FINISHED' % os.getpid())

###############################################################################
class IncomeReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN IncomeReport")
        pdf_file_url = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            beginDate = self.kwargs.get('bDate')
            endDate = self.kwargs.get('eDate')
            reportType = self.kwargs.get('type')         

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reportType, beginDate, endDate, outputQ)
            spawn_request(reqId, runIncomeReport, params)

            # Get the report url and path.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###############################################################################
def runIncomeReport(reportType, beginDate, endDate, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        now = timezone.now()

        if not beginDate:
            beginDate = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
            endDate = beginDate

        beginDate += " 00:00:00"
        endDate   += " 23:59:59"

        try:
            bDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d %H:%M:%S")
            eDate = datetime.datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S")
            bDate = timezone.make_aware(bDate,timezone.get_default_timezone())
            eDate = timezone.make_aware(eDate,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            bDate = now
            eDate = now

        reportRange = "From " + str(bDate.month) + "-" + str(bDate.day) + \
            "-" + str(bDate.year) + " to " + str(eDate.month) + "-" + \
            str(eDate.day) + "-" + str(eDate.year)

        logger.info("Begin Date: %s" % str(bDate))
        logger.info("End Date: %s" % str(eDate))
        logger.info("Range: %s" % reportRange)
        logger.info("Type: %s" % reportType)

        logger.info("STARTED income report for " + str(bDate) + " through " + str(eDate))
        pdf = create_income_report(reportType, bDate, eDate, reportRange)
        logger.info("FINISHED income report for " + str(bDate) + " through " + str(eDate))

        # Return the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf, 
                                                       report_name="income", 
                                                       start_date=bDate, 
                                                       end_date=eDate)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))
    except Exception,e:
        logger.exception(e)

###################################################################################
class AccountTrailReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN AccountTrailReport")
        pdf_file_url  = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            reportDate = self.kwargs.get('date')
            accountId = self.kwargs.get('accountId')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reportDate, accountId, outputQ)
            spawn_request(reqId, runAccountTrailReport, params)

            # Get the report url.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###################################################################################
def runAccountTrailReport(reportDate, accountId, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        try:
            date = datetime.datetime.strptime(reportDate, "%Y-%m-%d")
            date = datetime.datetime.combine(date, datetime.time(23, 59, 59))
            date = timezone.make_aware(date,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            date = timezone.now()

        logger.info("STARTED report for " + str(date))
        pdf = create_account_trail_report(date)
        logger.info("FINISHED report for " + str(date))

        # Respond with the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf,
                                                       report_name="account_trail", 
                                                       start_date=date)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))
    except Exception, e:
        logger.info(str(e))

###################################################################################
class AccountAuditReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN AccountAuditReport")
        pdf_file_url  = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            beginDate = self.kwargs.get('bDate')
            endDate = self.kwargs.get('eDate')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (beginDate, endDate, outputQ)
            spawn_request(reqId, runAccountAuditReport, params)

            # Get the report url.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###############################################################################
def runAccountAuditReport(beginDate, endDate, outputQ):
    logger.info('Account Audit PID: %d' % os.getpid())
    try:
        try:
            bDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
            bDate = datetime.datetime.combine(bDate, datetime.time(0, 0, 0))
            bDate = timezone.make_aware(bDate,timezone.get_default_timezone())

            eDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")
            eDate = datetime.datetime.combine(eDate, datetime.time(23, 59, 59))
            eDate = timezone.make_aware(eDate,timezone.get_default_timezone())

        except Exception, e:
            logger.exception(e)
            date = timezone.now()

        logger.info("Begin Date: %s" % str(bDate))
        logger.info("End Date: %s" % str(eDate))

        pdf = create_account_audit_report(bDate, eDate)
        logger.info("FINISHED account audit report")

        # Respond with the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf,
                                                       report_name="account_audit", 
                                                       start_date=eDate)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))

    except Exception, e:
        logger.exception(e)

###################################################################################
class OwnerInfoItem:
    def __init__(self):
        self.account = None;
        self.owner = None;

    def __unicode__(self):
        return '%s' % (self.account)

###################################################################################
class ExportReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN ExportReport")
        zip_file_url = "/report_error/"
        zip_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((zip_file_url, zip_file_path))
            params = (reqId, outputQ,)
            spawn_request(reqId, runExportReport, params)

            # Get the report url.
            (zip_file_url, zip_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        zip_file = {'url'  : zip_file_url, 
                    'path' : zip_file_path}
        response = HttpResponse(json.dumps(zip_file), 
                                content_type='application/json')
        return response

###################################################################################
def runExportReport(reqId, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        start_time = time.time() * 1000;

        # Construct a file name for a ZIP archive.
        zip_file_name_format = '{:' + settings.REPORT_DIR + '/export/export_%Y_%m_%d_%H_%M_%S.zip}'
        zip_file = zip_file_name_format.format(datetime.datetime.now())

        # Create and open an in-memory ZIP archive for writing of exported data.
        zipbuf = cStringIO.StringIO()
        zf = zipfile.ZipFile(zipbuf, "w", zipfile.ZIP_DEFLATED, False)

        # Update the request with items to be deleted if cancelled.
        update_request(reqId, (default_storage.path(zip_file),))
        
        #
        # Export accounts.
        #
        logger.info("exporting accounts ...")
        accounts = Account.objects.all().order_by("orig_id");

        # Write account header a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|ADDRESS|BALANCE|PMT PLAN\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each account.
        for x in accounts :
            if x.is_payment_plan: paymentPlan = "Y"
            else: paymentPlan = "N"
           
            ss = "" + x.acct_id + "|" + x.orig_id + "|" + \
                x.unit_address + " UNIT " + str(x.unit_number) + "|" + \
                str(x.balance)  + "|" + paymentPlan + "\n"
            buf.write(ss)

        # Save accounts to the ZIP file.
        zf.writestr("accounts.txt", buf.getvalue())

        #
        # Export entries.
        #
        logger.info("exporting entries ...")
        entries = Entry.objects.all().order_by("account__orig_id", "datetime");

        # Write entry header to a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|DATE|AMOUNT|CATEGORY|MEMO|BALANCE|USER|TIMESTAMP\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each entry.
        for x in entries:
            ss = "" + x.account.acct_id + "|" + x.account.orig_id + "|" + \
                x.datetime.strftime("%m/%d/%Y") + "|" + str(x.amount) + "|" \
                + str(x.category) + "|" + x.memo + "|" + str(x.balance) + "|" \
                + x.user + "|" + x.timestamp.strftime("%m/%d/%Y") + "\n"
            buf.write(ss)

        # Save account entries to the ZIP file.
        zf.writestr("entries.txt", buf.getvalue())

        #
        # Export owners.
        #
        logger.info("exporting owners ...")
        owners = Owner.objects.all()
        owner_info = [] 

        # Write owner header to a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|FIRST NAME|MIDDLE NAME|LAST NAME|HOME PHONE|CELL PHONE|EMAIL|ADDRESS|CITY|STATE|ZIP\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each owner.
        for x in owners:
           for y in x.account.all():
               o = OwnerInfoItem()
               o.owner = x
               o.account = y
               owner_info.append(o)

        owner_info.sort(key=lambda x: x.account.orig_id)

        for x in owner_info:
            ss = "" + x.account.acct_id + "|" + x.account.orig_id + "|" + \
                x.owner.first_name + "|" + x.owner.middle_name + "|" + \
                x.owner.last_name + "|" + x.owner.home_phone + "|" + \
                x.owner.cell_phone + "|" + x.owner.email + "|" \
                + x.owner.address + "|" + x.owner.city + "|" + \
                x.owner.state + "|" + x.owner.zip + "\n"
            buf.write(ss)

        # Save onwers to the ZIP file.
        zf.writestr("owners.txt", buf.getvalue())
        
        #
        # Export leases.
        #
        logger.info("exporting leases ...")
        leases = Lease.objects.all().order_by("account__orig_id");

        # Write lease header to a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|START DATE|END DATE|MONTHLY RENT\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each lease.
        for x in leases:
            str_start_date = ""
            str_end_date = ""
            if isinstance(x.start_date, datetime.date): 
                str_start_date = x.start_date.strftime("%m/%d/%Y")
            if isinstance(x.end_date, datetime.date): 
                str_end_date = x.end_date.strftime("%m/%d/%Y")

            ss = "" + x.account.acct_id + "|" + x.account.orig_id + "|" + \
                str_start_date + "|" + str_end_date + "|" + \
                str(x.monthly_rent) + "\n"
            buf.write(ss)

        # Save leases to the ZIP file.
        zf.writestr("leases.txt", buf.getvalue())

        #
        # Export tenants.
        #
        logger.info("exporting tenants ...")
        tenants = Tenant.objects.all().order_by("lease__account__orig_id");

        # Write tenant header to a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|FIRST NAME|MIDDLE NAME|LAST NAME|HOME PHONE|CELL PHONE|EMAIL|OWNER RELATIVE\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each tenant.
        for x in tenants:
            if x.is_owners_relative: owner_relative = "Y"
            else: owner_relative = "N"

            if x.lease is None:
                logger.info("No lease for tenant '{0}'".format(x))
                continue
           
            ss = "" + x.lease.account.acct_id + "|" + \
                x.lease.account.orig_id + "|" + x.first_name + "|" + \
                x.middle_name + "|" + x.last_name + "|" + x.home_phone + \
                "|" + x.cell_phone + "|" + x.email + "|" + owner_relative \
                + "\n"
            buf.write(ss)

        # Save tenants to the ZIP file.
        zf.writestr("tenants.txt", buf.getvalue())

        #
        # Export vehicles.
        #
        logger.info("exporting vehicles ...")
        vehicles = Vehicle.objects.all().order_by("account__orig_id");

        # Write vehicle header to a string buffer.
        ss = "ACCT_ID|ORIG_ACCT_ID|YEAR/MAKE/MODEL|COLOR|LICENSE PLATE\n"
        buf = cStringIO.StringIO()
        buf.write(ss)

        # Write each vehicle.
        for x in vehicles:
            if x.account is None:
                logger.info("No account for vehicle '{0}'".format(x))
                continue

            ss = "" + x.account.acct_id + "|" + \
                x.account.orig_id + "|" + x.year_make_and_model + "|" + \
                x.color + "|" + x.license_plate + "\n"
            buf.write(ss)

        # Save vehicles to the ZIP file.
        zf.writestr("vehicles.txt", buf.getvalue())

        #
        # Store the zip file in the default storage.
        #
        logger.info("saving the ZIP file ...")
        zf.close()
        default_storage.save(zip_file, ContentFile(zipbuf.getvalue()))

        # Increment the number of files in the list file.
        update_list_file(True, settings.REPORT_DIR + "/export/")

        # Provide URL to the stored ZIP file.
        zip_file_url = default_storage.url(zip_file)
        logger.info("ZIP URL: %s" % zip_file_url)

        # Provide the absolute path to the stored ZIP file.
        zip_file_path = "/" + os.path.basename(default_storage.location) + "/" + zip_file
        logger.info("ZIP PATH: %s" % zip_file_path)

        # Compute elapsed time.
        elapsed_time = (time.time() * 1000) - start_time
        logger.info("Elapsed Time %d" % elapsed_time)

        # Return the ZIP archive's URL and path to the calling process.
        while(not outputQ.empty()):
            outputQ.get() 
        outputQ.put((zip_file_url, zip_file_path))
    except Exception, e:
        logger.exception(e)

###############################################################################
class LeaseReport(StaffuserRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        logger.info("IN LeaseReport")
        pdf_file_url  = "/report_error/"
        pdf_file_path = "/report_error/"
        try:
            # Extract request parameters.
            reqId = self.kwargs.get('reqId')
            reportType = self.kwargs.get('type')
            date = self.kwargs.get('date')

            # Spawn the request process.
            outputQ = multiprocessing.Queue()
            outputQ.put((pdf_file_url, pdf_file_path))
            params = (reportType, date, outputQ)
            spawn_request(reqId, runLeaseReport, params)

            # Get the report url.
            (pdf_file_url, pdf_file_path) = outputQ.get()
        except Exception, e:
            logger.exception(e)

        pdf_file = {'url'  : pdf_file_url, 
                    'path' : pdf_file_path}
        response = HttpResponse(json.dumps(pdf_file), 
                                content_type='application/json')
        return response

###############################################################################
def runLeaseReport(reportType, reportDate, outputQ):
    logger.info('PID: %d' % os.getpid())
    try:
        try:
            date = datetime.datetime.strptime(reportDate, "%Y-%m-%d")
            date = datetime.datetime.combine(date, datetime.datetime.today().time())
            date = timezone.make_aware(date,timezone.get_default_timezone())
        except Exception, e:
            logger.exception(e)
            date = timezone.now()

        logger.info("STARTED generating " + str(reportType) + " lease report for " + str(date))

        if reportType == "fha":
            pdf = create_fha_lease_report(date)
        elif reportType == "vos":
            pdf = create_vos_lease_report(date)
        else:
            pdf = create_expired_lease_report(date)

        logger.info("FINISHED generating " + str(reportType) + " lease report for " + str(date))

        # Respond with the url to the generated report.
        pdf_file_url, pdf_file_path = save_pdf_to_file(pdf,
                                                       report_name=reportType + "_lease",
                                                       start_date=date)
        while(not outputQ.empty()):
            outputQ.get()
        outputQ.put((pdf_file_url, pdf_file_path))
    except Exception,e:
        logger.exception(e)

##############################################################################
@login_required
def cancel_report(request, reportType, reqId):
    logger.info("type: %s, reqId: %s" % (reportType, reqId))
    cancel_request(reqId)
    response = HttpResponse("Cancelled req %s for %s report" % (reqId, reportType), 
                            content_type='text/plain')
    return response
