#!/bin/bash
#
# Copyright (c) 2016 imm studios, z.s.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
##############################################################################
## COMMON UTILS

ORIG_DIR=`pwd`
BASE_DIR=$( cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )
TEMP_DIR=/tmp/$(basename "${BASH_SOURCE[0]}")

cd ${BASE_DIR}

function critical_error {
    printf "\n\033[0;31mInstallation failed\033[0m\n"
    cd $ORIG_DIR
    exit 1
}

function finished {
    printf "\n\033[0;92mInstallation completed\033[0m\n"
    cd $ORIG_DIR
    exit 0
}

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   critical_error
fi

if [ ! -d $TEMP_DIR ]; then
    mkdir $TEMP_DIR || critical_error
fi

## COMMON UTILS
##############################################################################

DB_USER="nebula"
DB_PASS="nebula"
DB_NAME="smartcoder"

SCRIPT_PATH="/tmp/smartcoder.sql"

function create_user {
    echo "Creating DB user"
    echo "
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
    " > ${SCRIPT_PATH}
    su postgres -c "psql --file=${SCRIPT_PATH}" || return 1
    rm ${SCRIPT_PATH}
}

function create_db {
    echo "Creating DB"
    echo "
        DROP DATABASE IF EXISTS ${DB_NAME};
        CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
    " > ${SCRIPT_PATH}
    su postgres -c "psql --file=${SCRIPT_PATH}" || return 1
    rm ${SCRIPT_PATH}
}

function create_schema {
    echo "Creating DB schema"
    export PGPASSWORD="${DB_PASS}";
    psql -h localhost -U ${DB_USER} ${DB_NAME} --file=${BASE_DIR}/support/schema.sql || return 1
}

echo ""
echo ""

if [ -z $DB_USER ] || [ -z $DB_PASS ] || [ -z $DB_NAME ]; then
    echo ""
    echo "DB connection params unspecified"
    critical_error
fi

if !(service postgresql status > /dev/null); then
    echo "This script must run on the DB server."
    while true; do
        read -p "Do you wish to install Postgresql server now??" yn
        case $yn in
            [Yy]* ) install_postgres || critical_error; break;;
            [Nn]* ) critical_error;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi

create_user || critical_error
create_db || critical_error
create_schema || critical_error
finished
