#!/bin/bash
set -e

# Create the recall_admin user if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    DO
    \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'recall_admin') THEN
            CREATE USER recall_admin WITH PASSWORD '$POSTGRES_PASSWORD';
        END IF;
    END
    \$\$;

    -- Make sure recall_admin has proper permissions
    ALTER USER recall_admin WITH SUPERUSER;
EOSQL

# Create the recall_db database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    SELECT 'CREATE DATABASE recall_db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'recall_db')\gexec
    
    GRANT ALL PRIVILEGES ON DATABASE recall_db TO recall_admin;
EOSQL

# Connect to recall_db and create schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "recall_db" <<EOSQL
    -- Create schema if it doesn't exist
    CREATE SCHEMA IF NOT EXISTS recall_schema;
    
    -- Grant all privileges on schema to recall_admin
    GRANT ALL ON SCHEMA recall_schema TO recall_admin;
    
    -- Set default privileges for future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA recall_schema 
    GRANT ALL ON TABLES TO recall_admin;
    
    -- Create extension if needed
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL 