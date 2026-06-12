# Local PostgreSQL fixture — setup reference

The live-PG probes (`pypy/tests/test_issue_46_*.py`) and bug-hunt reproductions run against a local PostgreSQL instance. This file is the single source for that setup so a fresh machine (or fresh LLM session) can rebuild it.

## Instance

- PostgreSQL **18.4**, native Windows install (not Docker)
- Windows service: `postgresql-x64-18` (auto-start; `Start-Service postgresql-x64-18` if stopped)
- Host `localhost`, port `5432`
- Superuser: `postgres` / password `tina4test`
- psql binary: `C:\Program Files\PostgreSQL\18\bin\psql.exe`
- GUI client: DBeaver (connections saved in its workspace config), plus psql/psycopg2 for scripted repros

## Databases

| DB | Purpose |
|---|---|
| `tina4_bug46` | BH-46 reproduction fixture — `gift_cards` table mirroring upstream reporter's setup |
| `tina4testingdb` | General-purpose testing — `items` demo table (see `pypy/tests/hello_pg.py`) |

## Rebuild from scratch

```powershell
$env:PGPASSWORD = "tina4test"
$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

# BH-46 fixture
& $psql -h localhost -U postgres -c "CREATE DATABASE tina4_bug46;"
& $psql -h localhost -U postgres -d tina4_bug46 -c @"
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
"@

# General testing DB
& $psql -h localhost -U postgres -c "CREATE DATABASE tina4testingdb;"
& $psql -h localhost -U postgres -d tina4testingdb -c "CREATE TABLE items (id SERIAL PRIMARY KEY, name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); INSERT INTO items (name) VALUES ('apple'), ('banana'), ('cherry');"
```

## Verify

```powershell
Get-Service postgresql-x64-18                              # Running?
& $psql -h localhost -U postgres -c "\l"                   # both DBs listed?
& $psql -h localhost -U postgres -d tina4_bug46 -c "\dt"   # gift_cards present?
cd pypy; uv run python tests/hello_pg.py                   # psycopg2 round-trip works?
```

The live-PG probes skip automatically (`pytest.mark.skipif`) when this instance is unreachable, so a machine without the fixture still runs the mocked probes cleanly.

## Methodology note

The fixture mirrors upstream reporters' setups as closely as the issue details allow (table layout, column types — e.g. `is_deleted BOOLEAN` for BH-46). When debugging a specific report, build the schema to match theirs; for generic doc verification, use `tina4testingdb`.
