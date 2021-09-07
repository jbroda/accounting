from django.conf.urls import patterns, include, url
from .views import SetupView, generate_jwt, postback 

urlpatterns = patterns('',
    # Account Views.
    url(r'^$', SetupView.as_view(), name='wallet'),
    url(r'^getjwt/$', generate_jwt),
    url(r'^postback/$', postback),
)