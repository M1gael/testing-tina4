#254 only helps if headers are still unsent, and under `tina4 serve` they never are, so the
native session never starts.

- **Repro (3.13.142):** on a fresh `tina4 init php` project with this issue's two routes, there
  is no `PHPSESSID`, and `/regen` returns 500 ("no active session").
- **Cause:** `serve` echoes its banner before the first request (`bin/tina4php:2218-2229`). The
  CLI SAPI has `output_buffering=0`, so `headers_sent()` is true, and
  `Router::startNativeSession()` skips `session_start()` (`Tina4/Router.php:1246`).
- **Why #254's test misses it:** the test runs with `TINA4_SUPPRESS=true`, so the banner never
  prints.
- **Why 3.13.138 seemed to work:** in single-process mode it shared one `$_SESSION` across all
  clients.

**Fix:** write the banner to `STDOUT`, as `Tina4\Log` does. The branch includes a test that
goes through `serve`:
https://github.com/tina4stack/tina4-php/compare/v3...MichaelC8E:tina4-php:fix/serve-leaves-headers-unsent-so-native-sessions-start

**Workaround:** `$request->session` works under `serve`.
