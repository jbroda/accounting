"""Common settings and globals."""

from os import environ
from os.path import abspath, basename, dirname, join, normpath
from sys import path, stderr

# Normally you should not import ANYTHING from Django directly
# into your settings, but ImproperlyConfigured is an exception.
from django.core.exceptions import ImproperlyConfigured

##############################################################################
def get_env_setting(setting, default=None):
    """ Get the environment setting or return exception """
    try:
        return environ[setting]
    except KeyError:
        error_msg = "ERROR: %s is not set, using default: %s" % (setting, default)
        print >>stderr, error_msg
        if default is None:
            raise ImproperlyConfigured(error_msg)
        else:
            return default 


########## PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = dirname(dirname(abspath(__file__)))

# Absolute filesystem path to the top-level project folder:
SITE_ROOT = dirname(DJANGO_ROOT)

# Site name:
SITE_NAME = basename(DJANGO_ROOT)

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(DJANGO_ROOT)
########## END PATH CONFIGURATION


########## DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
TEMPLATE_DEBUG = DEBUG
########## END DEBUG CONFIGURATION


########## MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ('Hidden Pond Admin', get_env_setting('SERVER_EMAIL','contact@xxxxxx.xx')),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
########## END MANAGER CONFIGURATION


########## DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        #'ENGINE':  'django.db.backends.sqlite3',
        #'NAME':    normpath(join(DJANGO_ROOT, 'default.db')),
        'ENGINE':   'django.db.backends.postgresql_psycopg2',
        'NAME':     get_env_setting('DB_NAME', 'hiddenpond_db'),
        'USER':     get_env_setting('DB_USER', 'hiddenpond'),
        'PASSWORD': get_env_setting('DB_PASSWORD', 'XXXXXXXXX'),
        'HOST':     get_env_setting('DB_HOST', '127.0.0.1'),
        'PORT':     get_env_setting('DB_PORT', 5432),
        'CONN_MAX_AGE': 60
    }
}
########## END DATABASE CONFIGURATION


########## GENERAL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'America/Chicago'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
########## END GENERAL CONFIGURATION


########## MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = normpath(join(SITE_ROOT, 'media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
########## END MEDIA CONFIGURATION


########## STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = normpath(join(SITE_ROOT, 'assets'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    normpath(join(SITE_ROOT, 'static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
########## END STATIC FILE CONFIGURATION


########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key should only be used for development and testing.
SECRET_KEY = r"#jf%5e+u=db20)8-o+54s#$&h6o1__-d-5xgt7u@4k4zp^q&2b"
########## END SECRET CONFIGURATION


########## SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []
########## END SITE CONFIGURATION


########## FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    normpath(join(SITE_ROOT, 'fixtures')),
)
########## END FIXTURE CONFIGURATION


########## TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
TEMPLATE_DIRS = (
    normpath(join(SITE_ROOT, 'templates')),
)
########## END TEMPLATE CONFIGURATION


########## MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
MIDDLEWARE_CLASSES = (
    # Default Django middleware.
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cuser.middleware.CuserMiddleware',
)
########## END MIDDLEWARE CONFIGURATION


########## URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = '%s.urls' % SITE_NAME
########## END URL CONFIGURATION


########## APP CONFIGURATION
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    'django.contrib.humanize',

    # Admin panel and documentation:
    'django.contrib.admin',
    'django.contrib.admindocs',
)

THIRD_PARTY_APPS = (
    'registration',      # user registration
    'registration.contrib.notification', # user registration notification
    'haystack',          # search
    'django_dropbox',    # Django Storage for Dropbox
    'reversion',         # django-reversion: model version control
    'reversion_compare', # diff support for django-reversion
    'cuser',             # current user
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'hiddenpond',
    'accounting',
    'payment',
    'regsupplement',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
########## END APP CONFIGURATION


########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

ERROR_LOG = environ.get('HP_ERROR_LOG')
if not ERROR_LOG:
    ERROR_LOG = normpath(join(environ.get('TEMP',SITE_ROOT), 'hp_error.log'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            #'format': '%(levelname)s %(message)s'
            'format': '%(asctime)s %(levelname)s %(funcName)s (line:%(lineno)d) %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'simple',
            'filename': ERROR_LOG,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends' : {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
        },
        'reversion_compare': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
        },
        'reversion': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
        },
        'elasticsearch': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
        },
        'xhtml2pdf': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'ERROR',
        },
        'accounting': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        },
        'payment': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        },
        'regsupplement': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        },
        'registration': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        },
        'django_dropbox.storage': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        },
        'hiddenpond': {
            'handlers': ['console', 'logfile', 'mail_admins'],
            'level': 'DEBUG',
        }
    }
}
########## END LOGGING CONFIGURATION

########## AUTH CONFIGURATION 
AUTH_USER_MODEL = 'hiddenpond.MyUser'
LOGIN_URL =  '/login/'
LOGOUT =  '/logout/'
LOGIN_REDIRECT_URL = '/'
########## END AUTH CONFIGURATION

########## WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME
########## END WSGI CONFIGURATION

########## django.registration CONFIGURATION
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = True
REGISTRATION_SUPPLEMENT_CLASS = 'regsupplement.models.MyRegistrationSupplement'
########## END django.registration CONFIGURATION

########## EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = get_env_setting('EMAIL_HOST', '127.0.0.1')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = get_env_setting('EMAIL_HOST_PASSWORD','')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
EMAIL_HOST_USER = get_env_setting('EMAIL_HOST_USER','')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = get_env_setting('EMAIL_PORT',587)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = get_env_setting('SERVER_EMAIL','')
DEFAULT_FROM_EMAIL = SERVER_EMAIL

#EMAIL_HOST = 'smtp.sendgrid.net'
#EMAIL_HOST_USER = get_env_setting('SENDGRID_USERNAME')
#EMAIL_HOST_PASSWORD = get_env_setting('SENDGRID_PASSWORD')
########## END EMAIL CONFIGURATION

########## haystack CONFIGURATION
HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
########## END haystack CONFIGURATION

########## static media CONFIGURATION
REPORT_DIR = 'reports'
LEASE_DIR = 'leases'
########## END static media CONFIGURATION

########## accounting CONFIGURATION
ASSESSMENT = 195.00
DELINQUENT_BALANCE = 300.00
GENERAL_ACCOUNT = 'P26001'
EXCLUDED_ACCOUNTS = [ GENERAL_ACCOUNT, 'B100921' ]
########## END accounting CONFIGURATION

# To suppress the warning 1_6.W001
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

########## django-reversion-compare CONFIGURATION
#ADD_REVERSION_ADMIN = False
########## END django-reversion-compare CONFIGURATION
