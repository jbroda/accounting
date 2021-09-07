#!/bin/bash

export PGDATABASE=hiddenpond_db
export PGUSER=hiddenpond
export PGHOST=hiddenpond.xxxxxxxxxxxx.us-east-2.rds.amazonaws.com
export PGPORT=5432
export PGPASSWORD=XXXXXXXXX

FILE="rel_dump__""`date -u +%Y_%m_%d__%H_%M_%S__%Z`"".sql"

echo "Dumping database '$PGDATABASE' from '$PGHOST' to "$FILE

pg_dump > $FILE

gzip $FILE
