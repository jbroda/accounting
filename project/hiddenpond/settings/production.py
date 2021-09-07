"""Production settings and globals."""

import os

from base import *

########## HOST CONFIGURATION
# See: https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
ALLOWED_HOSTS = ['localhost', 
                 '127.0.0.1', 
                 '.elasticbeanstalk.com',
                 '.azurewebsites.net', 
                 '.herokuapp.com',
                 '.pythonanywhere.com',
                 '.koding.io',
                 '.c9.io',
                 '.cloudapp.net',
                 '.amazonaws.com',
                 '.xxxxxxxx.xx']
########## END HOST CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
########## END EMAIL CONFIGURATION

########## CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
########## END CACHE CONFIGURATION


########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = get_env_setting('SECRET_KEY')
########## END SECRET CONFIGURATION

########## haystack CONFIGURATION
from urlparse import urlparse

es = urlparse(os.environ.get('SEARCHBOX_URL') or 'http://127.0.0.1:9200/')

port = es.port or 80

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': es.scheme + '://' + es.hostname + ':' + str(port),
        'INDEX_NAME': 'documents',
    },
}

if es.username:
    HAYSTACK_CONNECTIONS['default']['KWARGS'] = {"http_auth": es.username + ':' + es.password}
########## END haystack CONFIGURATION

########## django-dropbox CONFIGURATION
DROPBOX_CONSUMER_KEY = 'XXXX'
DROPBOX_CONSUMER_SECRET = 'XXXXX'
DROPBOX_ACCESS_TOKEN = 'XXXXX'
DROPBOX_ACCESS_TYPE = 'dropbox'
########## END django-dropbox CONFIGURATION

########## file storage CONFIGURATION
DEFAULT_FILE_STORAGE = 'hiddenpond.settings.storage.MediaRootDropboxStorage'
#STATICFILES_STORAGE  = 'hiddenpond.settings.storage.StaticRootDropboxStorage'

#DEFAULT_FILE_STORAGE = 'hiddenpond.settings.storage.MediaRootS3BotoStorage'
#STATICFILES_STORAGE  = 'hiddenpond.settings.storage.StaticRootS3BotoStorage'

#DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE  = 'django.contrib.staticfiles.storage.StaticFilesStorage'
########## END file storage CONFIGURATION

################## uncomment for debugging the production website ############
## DEBUG = True
## TEMPLATE_DEBUG = DEBUG
##############################################################################
