# Does `migrate` fail when the database is unreachable?

Ledger row `f-cli-33`. Reported against tina4php 3.13.141: `tina4php migrate` exits 0 when
the database cannot be reached, so a deploy script carries on as if it had migrated.

Run on `origin/v3` **3.13.144** (php `50b08e76`, python `37d60025`, ruby `228b2cb`, nodejs
`38d68da`) and the Rust CLI `origin/main` `3dc1624` (installed `tina4` 3.8.77), Linux, PHP 8.4.26,
Ruby 3.4.10, Node 22.22, SQLite and a local PostgreSQL 18. MySQL shapes only reach "nothing listening"
or "driver missing" - no MySQL server here.

```bash
./prove.sh php    <tina4-php tree with vendor/>
./prove.sh python <tina4-python tree>          # PY=<python with psycopg2> for the postgres shapes
./prove.sh ruby   <tina4-ruby tree>
./prove.sh nodejs <tina4-nodejs tree with node_modules/>
PG=user:pass@127.0.0.1:5432 ./prove.sh ...      # postgres shapes run only if that server answers
```

## Result

| | php | python | ruby | nodejs | `tina4` (Rust) |
|---|---|---|---|---|---|
| unreachable port / bad credentials / no such database / unresolvable host | **exit 0** | 1 | 1 | 1 | passes the child's code through |
| unsupported scheme | **exit 0** | 1 | **exit 0** | 1 | |
| SQLite file cannot be opened | **exit 0** | 1 | 1 | 1 | |
| nothing configured | 1 (via `DATABASE_URL`) | defaults to SQLite | **exit 0** | defaults to SQLite | |
| a migration file errors | 1 | 1 | 1 | 1 | |
| `migrate:rollback` with a failing down migration | **exit 0** | 1 | 1 | 1 | |

The `tina4` wrapper is not at fault: `delegate_command` (`src/main.rs:1579`) exits with the
child's status. Run against both php trees, `tina4 migrate` returned 0 on stock and 255 on the fix.

## Mechanism

**php.** In a project, `bin/tina4php:2272` includes the project's `index.php`. That file boots
the App (`App::handle()` → `start()`), and `App.php:568` installs a global exception handler that
logs and **returns**. On PHP 8 a handler that returns ends the script with status 0. Booting then
reaches `autoMigrateOnStartup()` → `getDatabase()` (`App.php:729`, outside the `try` at `:734`),
and the connection throws. With `TINA4_AUTO_MIGRATE=false` the throw comes from the CLI's own
`App::getDatabase()` (`bin/tina4php:2279`) and ends up in the same handler. Without an
`index.php` the same failure is PHP's own fatal error (255), which is why the existing
`CliMigrateExitCodeTest` (no `index.php`, `DATABASE_URL`) never saw it.
Separately, `migrate:rollback` prints `Error rolling back …` and never exits non-zero
(`bin/tina4php:2386-2397`).

**ruby.** `Tina4.setup_database` (`lib/tina4.rb:985-990`) rescues a failed `Database.new` and
leaves `Tina4.database` nil. The migrate commands then print "No database configured" and
`return` (`lib/tina4/cli.rb:772-775`, and the same in `migrate:status` `:859` and
`migrate:rollback` `:902`). Connection errors on a scheme that parses come later, from inside
the migration runner, and are non-zero. A bad scheme, or no URL at all, exits 0.

## Fix (uncommitted, in `~/.cache/tina4-worktrees/`)

- php `fcli33-php`: the App handler calls `exit(255)` after logging when `PHP_SAPI === 'cli'`,
  which is PHP's own status for an uncaught exception. `migrate:rollback` exits 1 when a rollback
  errors.
- ruby `fcli33-rb`: the three commands call `exit_without_database`, which says why on stderr
  and exits 1.

```
php stock                                     php fix
BAD  exit=0   sqlite: file cannot be opened   ok   exit=255 sqlite: file cannot be opened
BAD  exit=0   unsupported scheme              ok   exit=255 unsupported scheme
BAD  exit=0   postgres: bad credentials       ok   exit=255 postgres: bad credentials
...  (all 8 failure shapes)                   ok   exit=0   sqlite: reachable, migration applies
ok   exit=1   sqlite: a migration errors      ok   exit=1   sqlite: a migration errors

ruby stock: unsupported scheme 0, auto-migrate off 0, nothing configured 0 -> fix: all 1
```

## Seen on the way, not fixed here

- nodejs: `tina4nodejs migrate` against a **working** PostgreSQL never exits. `runMigrations`
  returns without closing the adapter, and the open `pg` client (`orm/src/adapters/postgres.ts:137`)
  keeps the process alive. Its own ledger row.
- The report's second part is security-sensitive and is kept out of this public tree.
