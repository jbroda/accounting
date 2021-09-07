import logging
from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from .models import Account, Category, Entry, Owner, Lease, Tenant, Vehicle

##############################################################################
logger = logging.getLogger(__name__)

##############################################################################
class ModelVersionAdmin(CompareVersionAdmin):
    pass

##############################################################################
class OwnerInline(admin.StackedInline):
    model = Owner.account.through
    extra = 1

class AccountAdmin(ModelVersionAdmin):
    def name (self, account):
        owner = account.owner_set.first()
        return '{0}, {1}'.format(owner.last_name, owner.first_name) if owner else None

    inlines = [OwnerInline]
    list_display = ('acct_id', 'orig_id', 'balance', 'name', 'unit_address', 'unit_number')
    search_fields = ('acct_id', 'orig_id', 'owner__last_name', 'unit_address')
    ordering = ('acct_id',)
    list_per_page = 300

##############################################################################
class OwnerAdmin(ModelVersionAdmin):
    list_display = ('last_name', 'first_name')
    ordering = ('last_name','first_name',)
    search_fields = ('last_name', 'first_name')
    filter_horizontal = ('account',);

##############################################################################
class LeaseSortedByAccount(Lease):
    def account_id(lease):
        return lease.account.acct_id
    class Meta:
        proxy = True
        ordering = ('account_id',)

class TenantInline(admin.StackedInline):
    model = Tenant
    extra = 1

class LeaseAdmin(ModelVersionAdmin):
    inlines = [TenantInline]
    ordering = ('account',)
    list_per_page = 300

##############################################################################
class EntrySortedByTimestamp(Entry):
    class Meta:
        verbose_name = 'Entry Sorted By Timestamp'
        verbose_name_plural = 'Entries Sorted By Timestamp'
        proxy = True
        ordering = ('-timestamp',)

class EntrySortedByDate(Entry):
    class Meta:
        verbose_name = 'Entry Sorted By Date'
        verbose_name_plural = 'Entries Sorted By Date'
        proxy = True
        ordering = ('-datetime',)

class EntrySortedByAccount(Account):
    def owner(account):
        return account.owner_set.first()
    class Meta:
        verbose_name = 'Entry Sorted By Account'
        verbose_name_plural = 'Entries Sorted By Account'
        proxy = True
        ordering = ('acct_id',)

class EntryInline(admin.StackedInline):
    model = Entry
    can_delete = True 
    ordering  = ('-datetime',)
    extra = 1

class EntrySortedByAccountAdmin(ModelVersionAdmin):
    can_delete = False
    list_per_page = 300
    list_display = ('acct_id','owner','balance','unit_address','unit_number',)

    inlines = [EntryInline]

##############################################################################
admin.site.register(Account, AccountAdmin)
admin.site.register(Owner, OwnerAdmin)
admin.site.register(LeaseSortedByAccount, LeaseAdmin)
admin.site.register(Tenant, ModelVersionAdmin)
admin.site.register(Vehicle, ModelVersionAdmin)
admin.site.register(EntrySortedByTimestamp, ModelVersionAdmin)
admin.site.register(EntrySortedByDate, ModelVersionAdmin)
admin.site.register(EntrySortedByAccount, EntrySortedByAccountAdmin)
admin.site.register(Entry, ModelVersionAdmin)
admin.site.register(Category, ModelVersionAdmin)