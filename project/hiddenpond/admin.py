from django.contrib import admin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.utils.html import escape
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from django.contrib.admin.views.main import ChangeList
from reversion_compare.admin import CompareVersionAdmin
from reversion.models import Revision
from .models import MyUser

##############################################################################
#
# Configure log entry history in the Admin interface.
#
action_names = {
    ADDITION: 'Addition',
    CHANGE:   'Change',
    DELETION: 'Deletion',
}

User = get_user_model()

class FilterBase(admin.SimpleListFilter):
    def queryset(self, request, queryset):
        if self.value():
            dictionary = dict(((self.parameter_name, self.value()),))
            return queryset.filter(**dictionary)

class ActionFilter(FilterBase):
    title = 'action'
    parameter_name = 'action_flag'
    def lookups(self, request, model_admin):
        return action_names.items()

class UserFilter(FilterBase):
    """Use this filter to only show current users, who appear in the log."""
    title = 'user'
    parameter_name = 'user_id'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username)
            for u in User.objects.filter(pk__in =
                LogEntry.objects.values_list('user_id').distinct())
        )

class AdminFilter(UserFilter):
    """Use this filter to only show current Superusers."""
    title = 'admin'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username) for u in User.objects.filter(is_superuser=True))

class StaffFilter(UserFilter):
    """Use this filter to only show current Staff members."""
    title = 'staff'
    def lookups(self, request, model_admin):
        return tuple((u.id, u.username) for u in User.objects.filter(is_staff=True))

class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    #readonly_fields = LogEntry._meta.get_all_field_names()

    list_filter = [
        UserFilter,
        ActionFilter,
        'content_type',
        # 'user',
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
        'action_description',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        ct = obj.content_type
        repr_ = escape(obj.object_repr)
        try:
            href = reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id])
            link = u'<a href="%s">%s</a>' % (href, repr_)
        except NoReverseMatch:
            link = repr_
        return link if obj.action_flag != DELETION else repr_
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'

    def get_queryset(self, request):
        return super(LogEntryAdmin, self).get_queryset(request) \
            .prefetch_related('content_type')

    def action_description(self, obj):
        return action_names[obj.action_flag]
    action_description.short_description = 'Action'

admin.site.register(LogEntry, LogEntryAdmin)

##############################################################################
#
# Track changes to the user objects.
#

class ModelVersionAdmin(CompareVersionAdmin):
    pass

class MyUserAdmin(ModelVersionAdmin):
    pass

admin.site.register(MyUser, MyUserAdmin)

##############################################################################
#
# Configure Reversion revision history in the Admin interface.
#

class RevisionChangeList(ChangeList):  
    def url_for_result(self, result):  
        version = result.version_set.first()
        obj = version.object
        url = reverse("admin:%s_%s_change" %
                      (obj._meta.app_label, obj._meta.model_name), 
                      args=(obj.id,))
        url += 'history/'
        return url

class RevisionAdmin(admin.ModelAdmin):
    list_display = ("id", "date_created", "user", "comment", )
    list_display_links = ("date_created", )
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)
    list_filter = ("user", "comment")
    search_fields = ("user", "comment")

    def get_changelist(self, request, **kwargs):
        return RevisionChangeList 

admin.site.register(Revision, RevisionAdmin)