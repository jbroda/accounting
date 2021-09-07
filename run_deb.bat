set SECRET_KEY=kdsfa78sf79s8df7ds9fsdf

set SERVER_EMAIL="Hidden Pond"
set EMAIL_HOST=127.0.0.1
set EMAIL_HOST_USER=''
set EMAIL_HOST_PASSWORD=''
set EMAIL_PORT=587

set DB_HOST=127.0.0.1
set DB_NAME=hiddenpond_db
set DB_USER=hiddenpond
set DB_PASSWORD=XXXXXXXXX
set DB_PORT=5432

python project\manage.py runserver --settings=hiddenpond.settings.local
