# Does `tina4 serve --managed` leave a dead `/__dev_reload` socket the browser keeps dialling?

Yes. Reported as tina4stack/tina4#27's sibling, tina4stack/tina4#28, by @ChanBos.

Run against: **tina4-php 3.13.134** (`origin/v3` `e0df3a97`), CLI source at `origin/main`
`3a4377d`.

## Measured

Same framework, same debug mode, one flag apart:

| | `GET /__dev_reload` (websocket upgrade) | toolbar flag on `GET /` |
|---|---|---|
| `--managed` (what `tina4 serve` always passes) | **404** | `data-reload="1"` |
| without `--managed` | **101 Switching Protocols** | `data-reload="1"` |

The server stops serving the socket. The page it serves does not stop asking for it.

## Mechanism

The server side, in tina4-php:

- `Tina4/Server.php:397` — `$this->noReload = $isManaged || DotEnv::isTruthy(DotEnv::getEnv('TINA4_NO_RELOAD', 'false'));`
- `Tina4/Server.php:441` — `if ($this->isDebug && !$this->noReload)` guards **both** the
  `Router::websocket('/__dev_reload', ...)` registration and the initial `detectFileChanges()`.

The client side, also tina4-php — neither client consults `noReload`, because nothing exposes it:

- `Tina4/DevAdmin.php:3092` — `$reload = (self::$suppressReload || str_starts_with($path, '/__dev')) ? '0' : '1';`
  The only inputs are the AI-port suppression flag (`Server.php:1153`, unrelated) and the request
  path. `Server::$noReload` is not one of them.
- `Tina4/DevAdmin.php:3282` (inline toolbar reloader) — `connect()` dials
  `ws://<host>/__dev_reload`; its `close` handler is
  `startPoll(); setTimeout(connect, 2000);`. No attempt cap, no backoff. Poll interval 3000 ms,
  cleared only by a `ws` `open` that can never arrive.
- `src/public/js/tina4-dev-admin.min.js` (the `/__dev` dashboard bundle) — its own client to the
  same socket, reconnect `5e3` on close, plus an ungated `setInterval` poll of
  `/__dev/api/mtime` every `3e3`.

So an app page runs the first client and `/__dev` runs the second — on `/__dev` the inline one is
inert because the path starts with `/__dev`, which is why the issue's console trace comes from
the bundle.

The Rust CLI is not the wrong side here. It never mentions `/__dev_reload` — it POSTs
`/__dev/api/reload` (`src/watcher.rs:161`, `src/main.rs:933`) and passes `--managed` exactly as
documented at `src/main.rs:1186`. Reload still works: the POST bumps the mtime counter
(`Tina4/DevAdmin.php:308`) and the polling fallback picks it up. What is broken is that the
fallback is the only path, while both clients keep trying the primary one for ever.

## Wider than the issue says

**Under the supported workflow the WebSocket reload path is unreachable, always.** The framework
refuses to start unless it was launched by the CLI or `TINA4_OVERRIDE_CLIENT=true` is set, and
every CLI launch passes `--managed`. So `noReload` is true on every supported run, and
`Router::websocket('/__dev_reload')` is never registered for anyone. The `broadcastWebSocket(...,
'/__dev_reload')` call at `Tina4/DevAdmin.php:396` has no route to broadcast to, and
`tests/DevReloadWsTest.php` / `DualPortReloadTest.php` cover a configuration no user can reach
from `tina4 serve`. The control run above needed `TINA4_OVERRIDE_CLIENT=true` for exactly this
reason.

## Reproduce

```
./prove.sh
FORK=/path/to/tina4-php ./prove.sh
```

No browser: a raw upgrade request is enough to see whether the route exists, and the toolbar flag
is read straight out of the HTML. Framework classes are symlinked out of the fork; nothing is
installed and nothing is written into it.

## Bounds

- Both runs are Linux, PHP 8.4.25. The issue reports Windows 11; the gate is platform-independent.
- The console spam itself was not observed in a browser — what is observed is the 404 that causes
  it and the client code that retries on close. The retry intervals are read, not timed.
- Whether a dead socket plus a 3 s poll is a measurable load is not established here. The issue
  calls it a log flood; that is an operator judgement, not something measured.
