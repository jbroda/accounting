======================
Hidden Pond Accounting
======================

Deployment Environment
-------------------

Perform the following steps:

#. Create a "free-tier" instance of Ubuntu Server 16.04 LTS on AWS or Azure.

#. Add user 'jbroda'.

#. Clone the BitBucket accounting repository in '/home/jbroda/Web/hp'.

#. Update the instance: 'sudo apt update'

#. Install apache2 apache2-utils: 'sudo apt install apache2 apache2-utils'. 

#. Install libapache2-mod-wsgi: 'sudo apt install libapache2-mod-wsgi'.

#. Install python-dev: 'sudo apt install python-dev'.

#. Install GCC: 'sudo apt install gcc'.

#. Install Postgres SQL 9.6 client:
 
    * sudo add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main"

    * wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

    * sudo apt-get update

    * sudo apt-get install postgresql-client-9.6

#. Enable mod_rewrite: 'sudo a2enmod rewrite'

#. Enable mod_ssl: 'sudo a2enmod ssl'

#. Copy 'config/000-default.conf' to '/etc/apache2/sites-available'.

#. Copy 'cert/private.key' to '/etc/apache2/ssl'.

#. Copy 'cert/cloudflare_2016.crt' to '/etc/apache2/ssl'.

#. Create a Python virtual environment in '/home/jbroda/Web/hp/venv':

    * sudo apt install virtualenv

    * cd /home/jbroda/Web/hp

    * virtualenv --python=python2.7 venv

    * source venv/bin/activate

    * pip install --upgrade 'setuptools<45.0.0'

    * pip install -r requirements.txt

#. Create '/home/jbroda/Web/hp/mail_passwd.txt' wit the 'contact@xxxxxxxx.xx' password.

#. Restart the Apache 2 server: 'sudo service apache2 restart'.
