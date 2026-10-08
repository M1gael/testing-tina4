# An unreachable database at boot blanks every route

The setup is a tina4-php app whose `migrations/` holds a `.sql` file and whose
database cannot be reached. Under `php -S` (and so PHP-FPM), every route then
answers **200 OK with an empty body**. That includes `/health`, so a load
balancer reads the dead app as healthy. The auto-migrator's docblock promises "A
failure here is logged LOUD and the service STILL starts".

Upstream: tina4-php#276, case 2. Ledger: `f-orm-07`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/App.php:691`: `start()` calls `autoMigrateOnStartup()` whenever
  `migrations/*.sql` exists and `TINA4_AUTO_MIGRATE` is not off.
- `Tina4/App.php:737`: `self::getDatabase()` **connects**, and it sits outside the
  `try` that starts at `:743`. The connect failure leaves `start()` before routing.
- `Tina4/App.php:568-594`: the exception handler logs and returns without a
  status, so the request ends as an empty 200.

Disproof runs (both directions, on 3.13.148):

- Moving only the `getDatabase()` call inside the `try` (in a throwaway tree): the
  app serves its 404 page and `/health` JSON, and logs the failure.
- Stock with `TINA4_AUTO_MIGRATE=false` also serves, so the auto-migrator is the
  only boot step that touches the database.
- The handler-only fix (`f-auth-04`) turns the 200 into a 500. That is honest, but
  the app is still down.
- No password reached the log on stock or on the fix (a URL with `user:pw`,
  closed port).

## Run

```sh
TREE=<tina4-php tree> ./prove.sh                  # closed port 127.0.0.1:1
AUTO_MIGRATE=false TREE=<tree> ./prove.sh         # the kill-switch control
DBURL=postgres://u:pw@127.0.0.1:1/x KEEPLOG=/tmp/log TREE=<tree> ./prove.sh
```

Each cell runs in a temp copy of `app/` (with or without `migrations/`), so
nothing the app writes lands here.

## Before and after (PHP 8.4.26, Linux, PostgreSQL URL on a closed port)

```
stock 4891b8d0
migrations/ present        GET /        200      0 bytes
migrations/ present        GET /health  200      0 bytes
migrations/ present        log: auto-migration-failed=0 uncaught=3
control: no migrations/    GET /        404   1684 bytes  <!DOCTYPE html> ...
control: no migrations/    GET /health  200     96 bytes  { "status": "ok", ...

fix (wip/fauth04 on 4891b8d0)
migrations/ present        GET /        404   1684 bytes  <!DOCTYPE html> ...
migrations/ present        GET /health  200     99 bytes  { "status": "ok", ...
migrations/ present        log: auto-migration-failed=3 uncaught=0
```

Under `php -S` the auto-migrator runs on every request (tina4-php#277, ledger
`f-orm-02`). So the failure is logged per request, and each request attempts the
connect again. Against a host that drops packets instead of refusing them, every
request would wait for the connect timeout. That case has not been measured.

## Other ports (3.13.148, run)

`python/`, `ruby/` and `nodejs/` all keep serving, so they are clear for the
200. Each has its own logging fault:

- py (`f-orm-09`) and nd log the failure only at DEBUG, as "no database
  configured". nd's wording at the default level is "ORM not available".
- rb logs "Database connected" before the failure (`f-orm-10`).
- nd only runs startup migrations when `src/orm/` or `src/models/` exists
  (`f-orm-11`).
