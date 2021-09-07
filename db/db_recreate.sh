#!/bin/bash

usage() 
{
    echo Usage: $0 '[deb|rel]'
}

if [ $# -ne 1 ] || ([ $1 != 'deb' ] && [ $1 != 'rel' ])
then
    usage
    exit
fi

export PGDATABASE=hiddenpond_db
export PGUSER=hiddenpond
export PGPORT=5432
export PGPASSWORD=XXXXXXXXX

if [ $1 == 'deb' ] 
then
    PGHOST=127.0.0.1
else
    PGHOST=hiddenpond.xxxxxxxxxxx.us-east-2.rds.amazonaws.com
fi

echo "DB Host: $PGHOST"
echo "DB Name: $PGDATABASE"
echo "DB User: $PGUSER"
echo "Type 'YES' to _DESTROY_ and _CREATE_ a database '$PGDATABASE' on '$PGHOST'"
read Q
echo "You response: $Q"

if [ "$Q" == "YES" ]; then
    # Back it up first.
    FILE="rel_dump__""`date -u +%Y_%m_%d__%H_%M_%S__%Z`"".sql"
    echo "Backing up the database '$PGDATABASE' from '$PGHOST' to "$FILE
    pg_dump > $FILE
    gzip $FILE

    echo "Dropping '$PGDATABASE' ..."
    dropdb $PGDATABASE

    echo "Creating '$PGDATABASE' ..."
    createdb $PGDATABASE
    echo "Completed!"
else
    echo "Aborted!"
fi
