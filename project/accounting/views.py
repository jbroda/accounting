from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse_lazy
from django.core import serializers
from django.core.files.storage import default_storage
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.http import HttpRequest
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView, UpdateView, DeleteView
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from .models import Account, Owner, Lease, Tenant, Vehicle, Entry, Category, Report
from .forms import AccountEntryForm, EntryForm, AccountForm, OwnerForm, LeaseForm
from .forms import TenantForm, VehicleForm, ReportForm
from .utils import add_transaction_entry
from .cc_info import get_cook_county_info_resp
from .list_file import *
import logging
import sys
import json
import os
import re

##############################################################################
logger = logging.getLogger(__name__)

###############################################################################
LeaseFormSet = inlineformset_factory(Lease, Tenant, fields='__all__', extra=1)

###############################################################################
class AccountTransactionEntry(LoginRequiredMixin, ListView, FormView):
    model = Account
    form_class = AccountEntryForm
    success_url = '/accounting/'

    def get_context_data(self, **kwargs):
        context = super(AccountTransactionEntry, self).get_context_data(**kwargs)
        owner = self.request.user.owner
        if owner:
            context['account_list'] = owner.account.all()
        context['category_types'] = Category.TYPE_CHOICES
        context['categories'] = Category.objects.all()
        if self.request.POST:
            context['form'] = AccountEntryForm(self.request.POST)
        else:
            context['form'] = AccountEntryForm(initial={
                                'amount' : -settings.ASSESSMENT,
                                'date' : timezone.now(), 
                                'memo' : ''
                            })
        return context

    def form_valid(self, form):
        try:
            amount        = form.cleaned_data['amount']
            memo          = form.cleaned_data['memo']
            category_name = form.cleaned_data['category']
            date          = form.cleaned_data['date']
            account_ids   = form.data.getlist('accounts')

            if self.request.user.is_staff:
                accounts = Account.objects.filter(acct_id__in=account_ids)
                category = Category.objects.get(name=category_name)
                response = add_transaction_entry(self.request.user, 
                                                 accounts, 
                                                 category, 
                                                 amount, 
                                                 memo, 
                                                 date)
            else:
                reponse = "ERROR: user is not staff!"

            return HttpResponse(response)
        except Exception, e:
            logger.exception(e)
            print >>sys.stderr, "ERROR: " + str(e)
            return HttpResponse("ERROR: " + str(e))

    def form_invalid(self, form):
        try:
            msg = "INVALID: " + str(form.errors)
            return HttpResponse(msg)
        except Exception, e:
            logger.exception(e)
            print >>sys.stderr, "ERROR: " + str(e)
            return HttpResponse("ERROR: " + str(e))

###############################################################################
class AccountDetail(LoginRequiredMixin, DetailView):
    model = Account

    def get_context_data(self, **kwargs):
        context = super(AccountDetail, self).get_context_data(**kwargs)
        context['category_types'] = Category.TYPE_CHOICES
        context['categories'] = Category.objects.all()
        if self.request.POST:
            context['form'] = AccountEntryForm(self.request.POST)
        else:
            context['form'] =  AccountEntryForm(initial={
                                    'amount' : -settings.ASSESSMENT,
                                    'date' : timezone.now(), 
                                    'memo' : ''
                                })
        return context

###############################################################################
class AccountPinInfo(LoginRequiredMixin, DetailView):
    model = Account

    def get(self, request, *args, **kwargs):
        pin = self.kwargs.get('pin')
        resp = get_cook_county_info_resp(pin)
        if resp is None:
            strError = "timed out!"
            logger.error(strError)
            print >>sys.stderr, "ERROR: " + strError
            return HttpResponse("ERROR: " + strError)
        return resp

###################################################################################
class SuccessUrl(object):
    def get(self, acct_pk):
        if acct_pk:
            self.success_url = reverse_lazy('accounts:update',kwargs={'pk':acct_pk})
            return self.success_url
        else:
            strError = "SuccessUrl: account PK is missing!"
            logger.error(strError)
            print >>sys.stderr, "ERROR: " + strError
            return HttpResponse("ERROR: " + strError)

###############################################################################
class AccountUpdate(LoginRequiredMixin, UpdateView, SuccessUrl):
    model = Account
    form_class = AccountForm

    def get_form(self, form_class):
        if self.request.POST:
            post = self.request.POST
            if 'add_owner' in post:
                form = OwnerForm(self.request.POST)
            elif 'add_lease' in post:
                form = LeaseFormSet(self.request.POST, self.request.FILES, prefix='tenant')
            elif 'add_tenant' in post:
                form = TenantForm(self.request.POST)
            elif 'add_vehicle' in post:
                form = VehicleForm(self.request.POST)
            else:
                form = super(AccountUpdate, self).get_form(form_class)
        else:
            form = super(AccountUpdate, self).get_form(form_class)
        return form

    def get_context_data(self, **kwargs):
        context = super(AccountUpdate, self).get_context_data(**kwargs)
        acct_id = self.kwargs.get('pk')
        if not acct_id:
            strError = "AccountUpdate.get_context_data(): account PK is missing!"
            logger.error(strError)
            print >>sys.stderr, "ERROR: " + strError
            return context

        try:
            # Get the existing lease.
            lease = Lease.objects.get(account=acct_id)
        except ObjectDoesNotExist:
            # Create a new lease.
            account = Account.objects.get(id=acct_id)
            lease = Lease()
            lease.account = account
            lease.save()

        self.owner_form = OwnerForm(initial={'account':[acct_id]})
        self.lease_form = LeaseForm(initial={'account':acct_id}, instance=lease)
        self.lease_formset = LeaseFormSet(instance=lease, prefix='tenant')
        self.tenant_form = TenantForm(initial={'lease':lease.pk})
        self.vehicle_form = VehicleForm(initial={'account':acct_id})

        if self.request.POST:
            post = self.request.POST
            if 'add_owner' in post:
                self.owner_form = OwnerForm(self.request.POST)
            elif 'add_lease' in post:
                self.lease_form = LeaseForm(self.request.POST)
                self.lease_formset = LeaseFormSet(self.request.POST, self.request.FILES, prefix='tenant')
            elif 'add_tenant' in post:
                self.tenant_form = TenantForm(self.request.POST)
            elif 'add_vehicle' in post:
                self.vehicle_form = VehicleForm(self.request.POST)

        context['vehicle_form'] = self.vehicle_form
        context['owner_form'] = self.owner_form
        context['lease_form'] = self.lease_form
        context['lease_formset'] = self.lease_formset
        context['tenant_form'] = self.tenant_form
        context['vehicle_form'] = self.vehicle_form

        context['owners'] = Owner.objects.all().order_by('last_name')
        context['tenants'] = Tenant.objects.all().order_by('last_name')
        context['vehicles'] = Vehicle.objects.all().order_by('year_make_and_model')
        return context
    
    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('pk'))

    def form_valid(self, form):
        if not self.request.user.is_staff:
            return HttpResponse("ERROR: user is not staff!")

        acct_id = self.kwargs.get('pk')
        if not acct_id:
            strError = "AccountUpdate.form_valid(): account PK is missing!"
            logger.error(strError)
            print >>sys.stderr, "ERROR: " + strError
            return super(AccountUpdate, self).form_valid(form)
        #
        # Process the owner form
        #
        if type(form) is OwnerForm:
            owner_id = int(form.data.get('existing_owner_id'))
            if owner_id and owner_id > 0:
                # Add the account to the existing owner.
                account = Account.objects.get(id=acct_id)
                owner = Owner.objects.get(id=owner_id)
                owner.account.add(account)
            else:
                # Add a new owner to the account.
                form.save();
        #
        # Process the lease form
        #
        elif type(form) is LeaseFormSet:
            logger.info("Got the lease form set!")
            return super(AccountUpdate, self).form_valid(form)
        #
        # Process the tenant form
        #
        elif type(form) is TenantForm:
            logger.info("Got the tenant form!")
            tenant_id = int(form.data.get('existing_tenant_id'))
            if tenant_id and tenant_id > 0:
                # Change the account of the existing tenant.
                account = Account.objects.get(id=acct_id)
                tenant = Tenant.objects.get(id=tenant_id)
                tenant.lease = account.lease
                tenant.save()
            else:
                # Add a new tenant to the account.
                form.save()
        #
        # Process the vehicle form
        #
        elif type(form) is VehicleForm:
            vehicle_id = int(form.data.get('existing_vehicle_id'))
            if vehicle_id and vehicle_id > 0:
                # Update the account of the existing vehicle
                account = Account.objects.get(id=acct_id)
                vehicle = Vehicle.objects.get(id=vehicle_id)
                vehicle.account = account
                vehicle.save()
            else:
                # Add a new vehicle to the account
                form.save()
        else:
            # Update the account.
            return super(AccountUpdate, self).form_valid(form)

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        # Re-create the account form on failure.
        acct_id = self.kwargs.get('pk')
        if acct_id:
            account = Account.objects.get(id=acct_id)
            form = self.form_class(instance=account)
        return super(AccountUpdate, self).form_invalid(form)

###################################################################################
class EntryUpdate(StaffuserRequiredMixin, UpdateView, SuccessUrl):
    model = Entry
    form_class = EntryForm

    def post(self, request, *args, **kwargs):
        try:
            pk = self.kwargs.get('pk')
            name = request.POST.get('name')
            value = request.POST.get('value')
            data = { name: value }
            entry = Entry.objects.get(pk=pk)
            form = EntryForm(data, instance=entry)
            if form.is_valid():
                form.save()
            else:
                raise Exception("Invalid data!")
            response = HttpResponse(request)
        except Exception,e:
            logger.exception(e)
            response = HttpResponseBadRequest(e)

        return response

###############################################################################
def render_to_json_response(context, **response_kwargs):
    data = json.dumps(context)
    response_kwargs['content_type'] = 'application/json'
    return HttpResponse(data, **response_kwargs)

###############################################################################
class OwnerDetail(LoginRequiredMixin, DetailView):
    model = Owner

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            owner = Owner.objects.get(id=kwargs.get('pk'))
            data = serializers.serialize("json", [ owner, ])
            return render_to_json_response(data)
        else:
            return super(OwnerDetail, self).get(request, *args, **kwargs)

###################################################################################
class OwnerCreate(StaffuserRequiredMixin, CreateView):
    model = Owner
    form_class = OwnerForm

    def get_context_data(self, **kwargs):
        context = super(OwnerCreate, self).get_context_data(**kwargs)
        acct_id = self.kwargs['acct_id']
        account = Account.objects.get(acct_id=acct_id)
        context['account'] = account
        return context

    def form_valid(self, form):
        return super(OwnerCreate, self).form_valid(form)

    def get_form(self, form_class):
        form = super(CreateView, self).get_form(form_class)
        acct_id = self.kwargs.get('acct_id')
        if acct_id:
            account = Account.objects.get(acct_id=acct_id)
            form.initial['account'] = [ account.id ]
        return form

###################################################################################
class OwnerUpdate(StaffuserRequiredMixin, UpdateView, SuccessUrl):
    model = Owner
    form_class = OwnerForm

    def get_context_data(self, **kwargs):
        context = super(OwnerUpdate, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#owners"

###################################################################################
class OwnerDelete(StaffuserRequiredMixin, DeleteView, SuccessUrl):
    model = Owner

    def get_context_data(self, **kwargs):
        context = super(OwnerDelete, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#owners"
        else:
            return '/accounting/'

    def post(self, request, *args, **kwargs):
        owner_id = kwargs.get('pk')
        acct_id = kwargs.get('acct_pk')
        if owner_id and acct_id:
            # Remove the account from the owner.
            owner = Owner.objects.get(id=owner_id)
            account = Account.objects.get(id=acct_id)
            owner.account.remove(account)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(OwnerDelete, self).post(request, *args, **kwargs)

###############################################################################
class LeaseDetail(LoginRequiredMixin, DetailView):
    model = Lease

###############################################################################
class LeaseCreate(StaffuserRequiredMixin, CreateView):
    model = Lease

###############################################################################
class LeaseUpdate(StaffuserRequiredMixin, UpdateView, SuccessUrl):
    model = Lease

    def get_context_data(self, **kwargs):
        context = super(LeaseUpdate, self).get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        lease = Lease.objects.get(id=pk)
        if self.request.POST:
            #self.lease_formset = LeaseFormSet(self.request.POST, self.request.FILES, instance=lease, prefix='tenant')
            self.lease_form = LeaseForm(self.request.POST, self.request.FILES)
            #self.tenant_form = TenantForm(self.request.POST)
        else:
            #self.lease_formset = LeaseFormSet(instance=lease, prefix='tenant')
            self.lease_form = LeaseForm(instance=lease)
            #self.tenant_form = TenantForm(initial={'lease':lease.pk})
        #context['lease_formset'] = self.lease_formset
        context['lease_form'] = self.lease_form
        #context['tenant_form'] = self.tenant_form
        context['tenants'] = Tenant.objects.all()
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk'))  + "#lease"

    def form_valid(self, form):
        context = self.get_context_data()
        #lease_formset = context['lease_formset']
        if form.is_valid(): #and lease_formset.is_valid():
            self.object = form.save()
            #lease_formset.instance = self.object
            #lease_formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(LeaseUpdate, self).form_valid(form)

###############################################################################
class LeaseDelete(StaffuserRequiredMixin, DeleteView, SuccessUrl):
    model = Lease

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#lease"

    def post(self, request, *args, **kwargs):
        lease_id = kwargs.get('pk')
        if lease_id:
            # Remove the tenants from the lease
            lease = Lease.objects.get(id=lease_id)
            for tenant in lease.tenant_set.all():
                tenant.lease = None
                tenant.save()
            # Reset lease fields
            lease.start_date = None
            lease.end_date = None
            lease.monthly_rent = None
            lease.lease_file.delete(False)
            lease.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(LeaseDelete, self).post(request, *args, **kwargs)

###############################################################################
class TenantDetail(LoginRequiredMixin, DetailView):
    model = Tenant

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            tenant = Tenant.objects.get(id=kwargs.get('pk'))
            data = serializers.serialize("json", [ tenant, ])
            return render_to_json_response(data)
        else:
            return super(TenantDetail, self).get(request, *args, **kwargs)

###################################################################################
class TenantUpdate(StaffuserRequiredMixin, UpdateView, SuccessUrl):
    model = Tenant
    form_class = TenantForm

    def get_context_data(self, **kwargs):
        context = super(TenantUpdate, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#lease"

###################################################################################
class TenantDelete(StaffuserRequiredMixin, DeleteView):
    model = Tenant
    success_url = '/accounting/'

###################################################################################
class TenantRemove(StaffuserRequiredMixin, DeleteView, SuccessUrl):
    model = Tenant

    def get_context_data(self, **kwargs):
        context = super(TenantRemove, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#lease"

    def post(self, request, *args, **kwargs):
        tenant_id = kwargs.get('pk')
        if tenant_id:
            # Remove the tenant from the lease.
            tenant = Tenant.objects.get(id=tenant_id)
            tenant.lease = None
            tenant.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(TenantRemove, self).post(request, *args, **kwargs)

###############################################################################
class VehicleDetail(LoginRequiredMixin, DetailView):
    model = Vehicle

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            vehicle = Vehicle.objects.get(id=kwargs.get('pk'))
            data = serializers.serialize("json", [ vehicle, ])
            return render_to_json_response(data)
        else:
            return super(VehicleDetail, self).get(request, *args, **kwargs)

###################################################################################
class VehicleUpdate(StaffuserRequiredMixin, UpdateView, SuccessUrl):
    model = Vehicle
    form_class = VehicleForm

    def get_context_data(self, **kwargs):
        context = super(VehicleUpdate, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#vehicles"

###################################################################################
class VehicleDelete(StaffuserRequiredMixin, DeleteView, SuccessUrl):
    model = Vehicle
    success_url = '/accounting/'

###################################################################################
class VehicleRemove(StaffuserRequiredMixin, DeleteView, SuccessUrl):
    model = Vehicle

    def get_context_data(self, **kwargs):
        context = super(VehicleRemove, self).get_context_data(**kwargs)
        acct_pk = self.kwargs.get('acct_pk')
        if acct_pk:
            account = Account.objects.get(id=acct_pk)
            context['account'] = account
        return context

    def get_success_url(self):
        return SuccessUrl.get(self, self.kwargs.get('acct_pk')) + "#vehicles"

    def post(self, request, *args, **kwargs):
        vehicle_id = kwargs.get('pk')
        if vehicle_id:
            # Remove the vehicle from the account.
            vehicle = Vehicle.objects.get(id=vehicle_id)
            vehicle.account = None
            vehicle.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(VehicleRemove, self).post(request, *args, **kwargs)

###############################################################################
class GenerateReports(StaffuserRequiredMixin, CreateView):
    model = Report 
    form_class = ReportForm

    def get_form(self, form_class):
        form = super(CreateView, self).get_form(form_class)
        form.initial['date'] =  timezone.now()
        return form

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)

        try:
            # Create dictionary with report info.
            reports = dict()

            report_dir = default_storage.path(settings.REPORT_DIR)
            report_url = default_storage.url(settings.REPORT_DIR)
            logger.info("REPORT DIR: %s, URL: %s" % (report_dir, report_url))

            # List directories under REPORT_DIR.
            dirs, files = default_storage.listdir(settings.REPORT_DIR)

            for dir in dirs:
                dir_path = os.path.join(settings.REPORT_DIR, dir)

                reports[str(dir)] = list() 

                # Check if the .list file exists under the current directory.
                if does_list_file_exist(dir_path):
                    reports[str(dir)] += (True,)
                    logger.info('LIST_FILE exists under {0}!'.format(dir_path))
                else:
                    logger.info('LIST_FILE does not exist under {0}!'.format(dir_path))

            context['reports'] = reports
        except Exception,e:
            logger.exception(e)
            print >>sys.stderr, "ERROR: " + str(e)
        return context

###############################################################################
class ListReportFiles(StaffuserRequiredMixin, ListView):
    model = Report

    def get(self, request, *args, **kwargs):
        try:
            # Extract request parameters.
            reportType = self.kwargs.get('type')
            logger.info('report type: {0}'.format(reportType))

            # Create a dictionary with report info.
            reports = dict()
            reports[reportType] = list()

            report_dir = default_storage.path(settings.REPORT_DIR)
            report_url = default_storage.url(settings.REPORT_DIR)
            logger.info("REPORT DIR: %s, URL: %s" % (report_dir, report_url))

            # List the contents of the report directory.
            dir_path = os.path.join(settings.REPORT_DIR, reportType)
            dirs, files = default_storage.listdir(dir_path)
            for file in files:
                if file == LIST_FILE: # Skip the .list file.
                    continue
                file_path = os.path.join(dir_path, file).replace('\\','/')
                file_url = default_storage.url(file_path)
                #logger.info("URL: %s" % file_url)
                m = re.match(r"\w+_(?P<yy>\d{4})_(?P<mo>\d{2})_(?P<dd>\d{2})_(?P<hh>\d{2})_(?P<mm>\d{2})_(?P<ss>\d{2})\.((pdf)|(zip))", file)
                #print "YY:", m.group('yy')
                #print "MO:", m.group('mo')
                #print "DD:", m.group('dd')
                #print "HH:", m.group('hh')
                #print "MM:", m.group('mm')
                #print "SS:", m.group('ss')
                report = { 
                    'url'  : file_url, 
                    'path' : "/" + os.path.basename(default_storage.location) + "/" + file_path,
                    'name' : os.path.basename(file_path) 
                }
                reports[reportType] = reports[reportType] + [ report ]

        except Exception,e:
            logger.exception(e)
            logger.debug("REPORTS: {0}".format(reports))

        return HttpResponse(json.dumps(reports), content_type = 'application/json; charset=utf8')
  
