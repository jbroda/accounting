from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView
from .views import AccountTransactionEntry, AccountDetail, AccountPinInfo, AccountUpdate
from .views import EntryUpdate
from .views import OwnerDetail, OwnerCreate, OwnerUpdate, OwnerDelete
from .views import LeaseDetail, LeaseCreate, LeaseUpdate, LeaseDelete
from .views import TenantDetail, TenantUpdate, TenantRemove, TenantDelete
from .views import VehicleDetail, VehicleUpdate, VehicleRemove, VehicleDelete
from .views import GenerateReports, ListReportFiles
from .reports import DelinquencyReport, TransactionsReport, StatementReport
from .reports import AccountTrailReport, ExportReport, LeaseReport, IncomeReport, AccountAuditReport
from .reports import EMailStatements
from .reports import cancel_report
from .tasks import apply_assessments, apply_late_fees

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Account Views.
    url(r'^$', AccountTransactionEntry.as_view(), name='list'),
    url(r'^enter/$', AccountTransactionEntry.as_view(), name='enter'),
    url(r'^account/(?P<pk>\d+)/enter/$', AccountTransactionEntry.as_view(), name='account_enter'),
    url(r'^account/$', RedirectView.as_view(url='/accounting', permanent=False), name='list'),
    url(r'^account/(?P<pk>\d+)/$', AccountDetail.as_view(), name='detail'),
    url(r'^account/(?P<pk>\d+)/update/$', AccountUpdate.as_view(), name='update'),
    url(r'^account/(?P<pk>\d+)/pin/(?P<pin>\d{2}-\d{2}-\d{3}-\d{3}-\d{4})/$', AccountPinInfo.as_view(), name='pin_info'),

    # Entry Views.
    url(r'^entry/(?P<pk>\d+)/update/$', EntryUpdate.as_view(), name='entry_update'),

    # Owner Views.
    url(r'^owner/(?P<pk>\d+)/$', OwnerDetail.as_view(), name='owner_detail'),
    url(r'^owner/add/(?P<acct_id>[BCP][0-9]{4}[1-6]{1})/$', OwnerCreate.as_view(), name='owner_add'),
    url(r'^owner/(?P<pk>\d+)/update/(?P<acct_pk>\d+)/$', OwnerUpdate.as_view(), name='owner_update'),
    url(r'^owner/(?P<pk>\d+)/delete/(?P<acct_pk>\d+)/$', OwnerDelete.as_view(), name='owner_delete'),
    url(r'^owner/(?P<pk>\d+)/delete/$', OwnerDelete.as_view(), name='owner_delete'),

    # Lease Views.
    url(r'^lease/(?P<pk>\d+)/$', LeaseDetail.as_view(), name='lease_detail'),
    url(r'^lease/add/(?P<acct_pk>\d+)/$', LeaseCreate.as_view(), name='lease_add'),
    url(r'^lease/(?P<pk>\d+)/update/(?P<acct_pk>\d+)/$', LeaseUpdate.as_view(), name='lease_update'),
    url(r'^lease/(?P<pk>\d+)/delete/(?P<acct_pk>\d+)/$', LeaseDelete.as_view(), name='lease_delete'),

    # Tenant Views.
    url(r'^tenant/(?P<pk>\d+)/$', TenantDetail.as_view(), name='tenant_detail'),
    url(r'^tenant/(?P<pk>\d+)/update/(?P<acct_pk>\d+)/$', TenantUpdate.as_view(), name='tenant_update'),
    url(r'^tenant/(?P<pk>\d+)/remove/(?P<acct_pk>\d+)/$', TenantRemove.as_view(), name='tenant_remove'),
    url(r'^tenant/(?P<pk>\d+)/delete/$', TenantDelete.as_view(), name='tenant_delete'),

    # Vehicle Views.
    url(r'^vehicle/(?P<pk>\d+)/$', VehicleDetail.as_view(), name='vehicle_detail'),
    url(r'^vehicle/(?P<pk>\d+)/update/(?P<acct_pk>\d+)/$', VehicleUpdate.as_view(), name='vehicle_update'),
    url(r'^vehicle/(?P<pk>\d+)/remove/(?P<acct_pk>\d+)/$', VehicleRemove.as_view(), name='vehicle_remove'),
    url(r'^vehicle/(?P<pk>\d+)/delete/$', VehicleDelete.as_view(), name='vehicle_delete'),

    # Report Views.
    url(r'^reports/$', GenerateReports.as_view(), name='generate_reports'),
    url(r'^reports/list/(?P<type>\w+)/$', ListReportFiles.as_view(), name='list_report_files'),

    url(r'^report/delinquency/$', DelinquencyReport.as_view(), name='delinquency_report'),
    url(r'^report/delinquency/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<date>\d{4}-\d{2}-\d{2})/$', DelinquencyReport.as_view(), name='delinquency_report'),

    url(r'^report/transaction/$', TransactionsReport.as_view(), name='transaction_report'),
    url(r'^report/transaction/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<type>\d{1})/(?P<bDate>\d{4}-\d{2}-\d{2})/(?P<eDate>\d{4}-\d{2}-\d{2})/$', TransactionsReport.as_view(), name='transaction_report'),

    url(r'^report/statement/$', StatementReport.as_view(), name='statement_report'),
    url(r'^report/statement/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<date>\d{4}-\d{2}-\d{2})/$', StatementReport.as_view(), name='statement_report'),
    url(r'^report/statement/(?P<date>\d{4}-\d{2}-\d{2})/(?P<accountId>\w+)/$', StatementReport.as_view(), name='statement_report'),
    url(r'^report/statement/(?P<date>\d{4}-\d{2}-\d{2})/(?P<accountId>\w+)/(?P<type>\w+)/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', StatementReport.as_view(), name='statement_report'),
    url(r'^report/statement/email/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', EMailStatements.as_view(), name='email_statements'),

    url(r'^report/income/$', IncomeReport.as_view(), name='income_report'),
    url(r'^report/income/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<type>\d{1})/(?P<bDate>\d{4}-\d{2}-\d{2})/(?P<eDate>\d{4}-\d{2}-\d{2})/$', IncomeReport.as_view(), name='income_report'),

    url(r'^report/account_trail/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<date>\d{4}-\d{2}-\d{2})/$', AccountTrailReport.as_view(), name='account_trail_report'),
    url(r'^report/account_trail/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<date>\d{4}-\d{2}-\d{2})/(?P<accountId>\w+)/$', AccountTrailReport.as_view(), name='account_trail_report'),

    url(r'^report/account_audit_report/$', AccountAuditReport.as_view(), name='account_audit_report'),
    url(r'^report/account_audit_report/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<bDate>\d{4}-\d{2}-\d{2})/(?P<eDate>\d{4}-\d{2}-\d{2})/$', AccountAuditReport.as_view(), name='account_audit_report'),

    url(r'^report/export/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', ExportReport.as_view(), name='export_report'),

    url(r'^report/lease/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<type>expired|fha|vos)/$', LeaseReport.as_view(), name='lease_report'),
    url(r'^report/lease/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/(?P<type>expired|fha|vos)/(?P<date>\d{4}-\d{2}-\d{2})/$', LeaseReport.as_view(), name='lease_report'),

    # Cancel report generation.
    url(r'^report/cancel/(?P<reportType>\w+)/(?P<reqId>\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/$', cancel_report),

    # Common tasks.
    url(r'^apply_assessments/$', apply_assessments),
    url(r'^apply_late_fees/$', apply_late_fees),
)
