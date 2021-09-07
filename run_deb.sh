#!/bin/sh

export SECRET_KEY=`cat secret_key.txt`

export SERVER_EMAIL="Hidden Pond"
export EMAIL_HOST=127.0.0.1
export EMAIL_HOST_USER=''
export EMAIL_HOST_PASSWORD=''
export EMAIL_PORT=587

export DB_HOST=127.0.0.1
export DB_NAME=hiddenpond_db
export DB_USER=hiddenpond
export DB_PASSWORD=XXXXXXXXX
export DB_PORT=5432

python project/manage.py runserver --settings=hiddenpond.settings.local
