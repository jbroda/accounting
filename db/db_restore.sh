#!/bin/bash

usage() 
{
    echo Usage: $0 '<file>.sql.gz'
}

if [ $# -ne 1 ]
then
    usage
    exit
fi

if [ ! -e $1 ]
then
    echo "File '$1' does not exist!"
    exit
fi

DB_FILE=$1
DB_UNZIPPED=${DB_FILE/.gz/}

export PGDATABASE=hiddenpond_db
export PGUSER=hiddenpond
export PGHOST=127.0.0.1
export PGHOST=hiddenpond.xxxxxxxxxxxx.us-east-2.rds.amazonaws.com
export PGPORT=5432
export PGPASSWORD=XXXXXXXXX

echo "DB File: $DB_FILE"
echo "DB Host: $PGHOST"
echo "DB Name: $PGDATABASE"
echo "DB User: $PGUSER"
echo "Type 'YES' to restore database '$PGDATABASE' on '$PGHOST' form '$DB_FILE'"
read Q
echo "Your response: $Q"

if [ "$Q" == "YES" ]; then
    echo "Uncompresing '$DB_FILE' ..."
    gunzip -f $DB_FILE

    echo "Dropping '$PGDATABASE' ..."
    dropdb $PGDATABASE

    echo "Creating '$PGDATABASE' ..."
    createdb $PGDATABASE

    echo "Restoring '$PGDATABASE' from '$DB_UNZIPPED' ..."
    psql < $DB_UNZIPPED

    echo "Compressing '$DB_UNZIPPED' ..."
    gzip $DB_UNZIPPED

    echo "Completed!"
else
    echo "Cancelled!"
fi
