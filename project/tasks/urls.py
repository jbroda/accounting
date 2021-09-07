from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView
from .views import AccountList

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^create_task/$', AccountList.as_view(), name='create_task'),
    url(r'^view_open_tasks/$', AccountList.as_view(), name='open_tasks'),
    url(r'^view_completed_tasks/$', AccountList.as_view(), name='completed_tasks'),
    url(r'^mark_complete/$', AccountList.as_view(), name='mark_complete'),
    url(r'^edit_desc/$', AccountList.as_view(), name='edit_desc'),
    url(r'^edit_prio/$', AccountList.as_view(), name='edit_prio'),
)
