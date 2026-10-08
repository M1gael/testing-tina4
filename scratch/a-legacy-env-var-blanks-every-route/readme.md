# A legacy env var blanks every route

tina4-php refuses to boot when a v3.11-era un-prefixed variable is set, such as
`DATABASE_URL`, `SECRET` or `SMTP_HOST`. Container platforms often set
`DATABASE_URL` for you. Under a front controller (`php -S`, PHP-FPM) the refusal
`exit(2)`s inside the request. Every route then answers **200 OK with an empty
body**, and the list of renames goes only to the server's stderr.

This is the class tina4-php#276's title names ("A failure inside App::start() is
answered with HTTP 200"), but not one of its two cases. Ledger: `f-misc-09`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/App.php:534`: `start()` calls `self::checkLegacyEnvVars()`.
- `Tina4/App.php:114-170`: the guard writes the box message to `php://stderr` and
  calls `exit(2)` (`:168`). In a web request, `exit()` ends the request normally,
  so the status stays 200.

## Run

```sh
TREE=<tina4-php tree> ./prove.sh
```

## Before and after (`out-3.13.148.txt`, PHP 8.4.26, Linux, `DATABASE_URL=sqlite:///legacy.db`)

```
stock 4891b8d0
TINA4_DEBUG=false GET /        200     0 bytes
TINA4_DEBUG=false GET /health  200     0 bytes
TINA4_DEBUG=true  GET /health  200     0 bytes

fix (wip/fauth04 on 4891b8d0)
TINA4_DEBUG=false GET /        500    13 bytes  Server Error
TINA4_DEBUG=false GET /health  500    13 bytes  Server Error
TINA4_DEBUG=true  GET /health  500  1051 bytes  (the rename list)
```

The fix calls `checkLegacyEnvVars(exit: PHP_SAPI === 'cli')`:

- A console still exits 2.
- A web request throws instead. The handler, which a web request now installs in
  the `App` constructor (`../a-short-secret-is-refused-with-a-stack-trace`), logs
  the reason and answers 500.

## Other ports (3.13.148, read)

py (`server.py:4175`), rb (`webserver.rb:56`) and nd (`server.ts:279-315`) all
refuse when the process starts, before anything listens. They are clear.
