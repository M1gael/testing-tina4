# Database::create refuses pgsql URLs

`Database::create('pgsql://...')`, and so `TINA4_DATABASE_URL=pgsql://...`, fails with
"Unsupported database scheme 'pgsql'". Yet `DatabaseUrl` maps `pgsql` to `postgres`,
and two docblocks show `pgsql://` URLs.

Upstream: tina4-php#280. The maintainer opened PR #281 with the same one-line fix; its
only CI failure is the stale `assertFalse(Database::isSupported('pgsql'))`. Ledger:
`f-orm-08`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/Database/Database.php:44-55`: `ADAPTER_MAP` has `postgres` and `postgresql`,
  not `pgsql`.
- `Tina4/DatabaseUrl.php:65` maps `pgsql` to `postgres`.
- History: `e4033aed` asserted pgsql supported. `cf808cfe` (2026-03-21) dropped it and
  flipped the test. `5a4bfd30` (2026-07-04) re-added it to `DatabaseUrl` only.

## Run

```sh
TREE=<tina4-php tree> php prove.php                   # every DatabaseUrl scheme, no server needed
TREE=<tree> PGURL=postgres://... php live.php         # live PostgreSQL
```

## Before and after (PHP 8.4.26, PostgreSQL 18.6)

```
stock: pgsql   Database::create   FAILED InvalidArgumentException: Unsupported database scheme 'pgsql'
       pgsql   App::getDatabase() FAILED (same)
fix:   pgsql   Database::create   row answer=42 via Database
       pgsql   App::getDatabase() row answer=42 via Database
```

The fix adds `'pgsql' => PostgresAdapter::class`. A property test checks that every
scheme `DatabaseUrl` accepts is one the factory accepts.

## Other ports (3.13.148)

- py: clear (`connection.py:195`).
- nd: clear.
- rb: accepts the scheme but hands the raw `pgsql://` URL to libpq, which rejects it.
  See `ruby/`.
