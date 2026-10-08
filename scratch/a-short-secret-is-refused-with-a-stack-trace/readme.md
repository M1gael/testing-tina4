# A short secret is refused with a stack trace

tina4-php refuses to boot when `TINA4_SECRET` is shorter than 32 bytes. Under a
front controller (`php -S`, PHP-FPM, Apache) `index.php` runs per request, so the
refusal answers the **client**, and Tina4 never sees it:

- `display_errors` on (PHP's default without a `php.ini`, as in the official
  Docker images): **200 OK** with "Fatal error: Uncaught RuntimeException", the
  stack trace and the framework's absolute paths.
- `display_errors` off: a bare 500.
- Either way Tina4's own log has nothing.

Upstream: tina4-php#276, case 1. Ledger: `f-auth-04`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/App.php:539`: `start()` calls `Auth::requireBootSecret()`, which throws at
  `Tina4/Auth.php:347`.
- `Tina4/App.php:568`: the exception handler is installed only later in `start()`,
  so PHP's default handler answers the throw.
- The 200 is PHP's rule, not Tina4's: an uncaught exception leaves the status at
  200 whenever PHP displays the error itself (checked with plain PHP, no Tina4).
- `Tina4/App.php:568-594`: the handler, once it does exist, logs and returns
  without setting a status, so a web request still ends as a 200.

## Run

```sh
TREE=~/.cache/tina4-worktrees/gi148-stock-php ./prove.sh   # stock
TREE=~/.cache/tina4-worktrees/fauth04 ./prove.sh           # the fix
```

`app/` is the project: `index.php` (requires `$TREE/vendor/autoload.php`), a plain
`/hello` route, and `/boom`, a route that throws after the handler is installed
(the control for what Tina4 does with an error it does see).

## Before and after (`out-3.13.148.txt`, PHP 8.4.26, Linux)

```
stock 4891b8d0
5-byte secret, display_errors=On    status=200  trace=YES  fwpaths=YES  tina4-log=no   BUG
5-byte secret, display_errors=Off   status=500  trace=no   fwpaths=no   tina4-log=no   BUG
32-byte secret, /hello  (control)   status=200
32-byte secret, /boom   (handler)   status=500

fix (wip/fauth04 on 4891b8d0)
5-byte secret, display_errors=On    status=500  trace=no   fwpaths=no   tina4-log=YES  ok
5-byte secret, display_errors=Off   status=500  trace=no   fwpaths=no   tina4-log=YES  ok
```

In a web request the fix installs the handlers in the `App` constructor, before
anything can refuse; a console still installs them in `start()`, as before. The
handler answers a web request with 500 `Server Error` (the message, never the trace
or paths, only with `TINA4_DEBUG=true`) unless output has already started. The same
branch fixes three siblings: `../an-unreachable-database-at-boot-blanks-every-route`,
`../a-legacy-env-var-blanks-every-route` and
`../a-bad-log-setting-is-refused-with-a-stack-trace`. The last was found by attacking
the first version of this fix, which installed the handlers at the top of `start()`
and so still missed a refusal from the constructor.

## Other ports (3.13.148, run)

`python/`, `ruby/` and `nodejs/` hold the same check. All three refuse a 20-byte
secret when the process starts: it exits 1, nothing listens, and the trace is
only on the console. They are clear.
