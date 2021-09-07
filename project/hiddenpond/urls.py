from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from haystack.views import SearchView
from .search import SearchResults, SimpleSearch 
from .media import serve_media, delete_media, serve_log
from registration.views import RegistrationView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Add django-inspectional-registration urls.
    url('^user/', include('registration.urls')),

    url(r'^login/$','django.contrib.auth.views.login'),
    url(r'^logout/$','django.contrib.auth.views.logout',{'next_page':'/'}),

    url(r'^$', login_required(TemplateView.as_view(template_name='index.html')),name='home'),

    # accounting app URLs.
    url(r'^accounting/', include('accounting.urls', namespace='accounts')),

    # payment app URLs.
    url(r'^payment/', include('payment.urls', namespace='accounts')),

    url(r'^report_error/', TemplateView.as_view(template_name='report_error.html')),

    #url(r'^search/',SimpleSearch.as_view(),name='search_results'),
    url(r'^search/',SearchResults(),name='haystack_search'),
    #url(r'^search/',SearchView(load_all=False)),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Serve static media files.
    url(r'^media/(?P<mediaType>\w+)/(?P<subType>\w+)/(?P<filename>\w+)\.(?P<fileExtension>\w+)$', serve_media),

    # Delete static media files
    url(r'^delete/media/(?P<mediaType>\w+)/(?P<subType>\w+)/(?P<filename>\w+)\.(?P<fileExtension>\w+)$', delete_media),

    # Serve the website log
    url(r'^log/$', serve_log),
)

"""
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
