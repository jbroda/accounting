#
# wsgi.py
#

import os
import sys

# Activate the virtual environment
HOME = '/home/jbroda/Web/hp'
activate_this = HOME + '/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Add project directory the system path.
path = HOME + '/project'
if path not in sys.path:
    sys.path.append(path)

# Read the secret key.
SECRET_KEY_FILE = HOME + '/secret_key.txt'
with open(SECRET_KEY_FILE) as f:
   secret_key = f.read()

# Misc environment variables.
os.environ['TEMP'] = '/tmp'
os.environ['DJANGO_SETTINGS_MODULE'] = 'XXXXXXXX.settings.production'
os.environ['SECRET_KEY'] = secret_key

### Admin Email ###
#ADMIN_EMAIL = 'admin@XXXXXXXX.us'
ADMIN_EMAIL = 'contact@XXXXXXXX.us'

# Read the mail password.
MAIL_PASSWD_FILE = HOME + '/mail_passwd.txt'
with open(MAIL_PASSWD_FILE) as f:
   mail_passwd = f.read()

### Email server settings ###
os.environ['SERVER_EMAIL']=ADMIN_EMAIL
os.environ['EMAIL_HOST']='smtp.XXXX.com'
os.environ['EMAIL_HOST_USER']=ADMIN_EMAIL
os.environ['EMAIL_HOST_PASSWORD']=mail_passwd
os.environ['EMAIL_PORT']='587'

### Database settings ###

# Azure
#os.environ['DB_HOST']='XXXXXXXX-db.postgres.database.azure.com'
#os.environ['DB_NAME']='XXXXXXXX-db'
#os.environ['DB_USER']='XXXXXXXX@XXXXXXXX-db'
#os.environ['DB_PASSWORD']='XXXXXXXXX$'

# AWS
os.environ['DB_HOST']='XXXXXXXX.XXXXXXXXXXX.us-east-2.rds.amazonaws.com'
os.environ['DB_NAME']='XXXXXXXX_db'
os.environ['DB_USER']='XXXXXXXX'
os.environ['DB_PASSWORD']='XXXXXXXXX'
os.environ['DB_PORT']='5432'

### Elasticsearch ##
os.environ['SEARCHBOX_URL']='http://paas:XXXXXXXXXXXXXXXXXX@bombur-us-east-1.searchly.com'
os.environ['SEARCHBOX_SSL_URL']='https://paas:XXXXXXXXXXXXXXXX@bombur-us-east-1.searchly.com'

import django.core.wsgi
application = django.core.wsgi.get_wsgi_application()
