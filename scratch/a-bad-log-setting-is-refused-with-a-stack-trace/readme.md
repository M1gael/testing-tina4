# A bad log setting is refused with a stack trace

tina4-php validates every `TINA4_LOG_*` variable when the `App` is constructed, and
refuses a bad one (`TINA4_LOG_FORMAT=xml`, an unknown level, a removed setting) by
throwing. Under a front controller (`php -S`, PHP-FPM, Apache) `index.php` builds an
`App` per request, so that refusal answers the **client**. With `display_errors` on
(PHP's default without a `php.ini`, as in the official Docker images), the client gets
**200 OK** with "Fatal error: Uncaught Tina4\LogConfigurationError", the stack trace
and the framework's absolute paths.

This is the class of tina4-php#276 ("A failure inside App::start() is answered with
HTTP 200"), one step earlier: the throw comes from the constructor, before `start()`
runs. It was found by attacking the fix for #276 case 1
(`../a-short-secret-is-refused-with-a-stack-trace`), which moved the handler to the
top of `start()` and so still missed it. Ledger: `f-misc-10`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/App.php:309`: the constructor calls `Log::configure()`.
- `Tina4/Log.php:865`: `resolveFormat()` throws `LogConfigurationError` for any format
  but `text` or `json`. The other `TINA4_LOG_*` checks throw the same way
  (`Log.php:271`, `:817`-`:940`).
- `Tina4/App.php:249-256`: the exception handler is installed only in `start()`, so
  nothing of Tina4's sees the throw, and PHP's own handler answers it.

## Run

```sh
TREE=<tina4-php tree> ./prove.sh
```

`app/index.php` is the front controller from the report: one `App` per request.

## Before and after (`out-3.13.148.txt`, PHP 8.4.26, Linux, `TINA4_LOG_FORMAT=xml`)

```
stock 4891b8d0
TINA4_DEBUG=false GET /        200   601 bytes  trace=YES fwpaths=YES  Fatal error:  Uncaught Tina4\LogConfigurationE
TINA4_DEBUG=false GET /health  200   601 bytes  trace=YES fwpaths=YES  Fatal error:  Uncaught Tina4\LogConfigurationE

fix (wip/fauth04 on 4891b8d0)
TINA4_DEBUG=false GET /        500    13 bytes  trace=no  fwpaths=no  Server Error
TINA4_DEBUG=false GET /health  500    13 bytes  trace=no  fwpaths=no  Server Error
TINA4_DEBUG=true  GET /health  500    56 bytes  trace=no  fwpaths=no  TINA4_LOG_FORMAT=xml is not valid; accepted: text, json
```

The server's own output names the setting on both trees.

The fix has two parts:

- In a web request the constructor installs the error capture before anything can
  refuse. On a console it is still installed in `start()`, as before, so tests that
  construct an `App` without starting it leak no handler.
- The handler's own logging is guarded. The logger is the thing that failed here, and
  asking it again from the handler threw out of the handler. PHP's `error_log()` takes
  the line instead.

## Other ports (3.13.148)

py, rb and nd boot once, when the process starts, before anything listens. A refusal
there reaches the console, never a client. That was shown by running each port with a
short secret (`../a-short-secret-is-refused-with-a-stack-trace`). Whether each port
validates `TINA4_LOG_FORMAT` at all has not been checked; this leak is not possible
there either way.
