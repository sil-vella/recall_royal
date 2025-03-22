#!/bin/bash
set -e

# Create the user with password from environment variable
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER recall_admin WITH PASSWORD '$POSTGRES_PASSWORD';
    ALTER USER recall_admin WITH SUPERUSER;
    CREATE DATABASE recall_db;
    GRANT ALL PRIVILEGES ON DATABASE recall_db TO recall_admin;
EOSQL

# Connect to recall_db and create extensions/schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "recall_db" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS recall_schema;
    ALTER SCHEMA recall_schema OWNER TO recall_admin;
    GRANT ALL ON SCHEMA recall_schema TO recall_admin;
EOSQL 