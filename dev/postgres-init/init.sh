#!/bin/bash
# Runs ONCE on first container start (empty data volume). Recreates the two
# fixtures the live-PG probes expect — see ../../CLAUDE.md "Local Postgres fixture".
# To re-run: docker compose down -v && docker compose up -d
set -e

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE tina4_bug46;
    CREATE DATABASE tina4testingdb;
EOSQL

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d tina4_bug46 <<-EOSQL
    CREATE TABLE gift_cards (
        id SERIAL PRIMARY KEY,
        created_by_email VARCHAR(200) NOT NULL,
        owned_by_email VARCHAR(200),
        amount NUMERIC(10,2) NOT NULL,
        is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO gift_cards (created_by_email, amount)
    VALUES ('schalk@codeinfinity.co.za', 100.00), ('schalk@codeinfinity.co.za', 50.00);
EOSQL

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d tina4testingdb <<-EOSQL
    CREATE TABLE items (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO items (name) VALUES ('apple'), ('banana'), ('cherry');
EOSQL
