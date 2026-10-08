# The dev toolbar loads for a peer it will refuse

With `TINA4_DEBUG=true`, tina4-php puts the dev toolbar into every HTML page, the 404
page and the 500 error overlay for **every** caller. `/__dev` itself only answers a
loopback peer, or a caller with a dedicated MCP token, on an allowed Host (ADR-0082). A
peer that gate refuses gets a toolbar on every page, and every one of its buttons
answers 403. Examples are a container's app browsed from the Docker host (the app sees
the gateway, 172.17.0.1) and a box on the LAN.

Upstream: tina4-php#279, reported from Docker Desktop on Windows 11. **Not
Windows-specific:** it reproduces on Linux. Ledger: `f-dev-02`.

## Mechanism (tina4-php 3.13.148, `4891b8d0`)

- `Tina4/Router.php:2594` `injectDevToolbar()` checks `TINA4_DEBUG` and the path, never
  the caller.
- `Tina4/ErrorOverlay.php:284` renders its own copy of the toolbar on the 500 overlay
  (fed from `Router.php:929`).
- `Tina4/DevAdmin.php` `guardRequest()` refuses the same caller on every `/__dev`
  request.

## Run

```sh
TREE=<tina4-php tree> ./prove.sh
```

Three probes:

- `peer.php`: a page and `/__dev` per peer, and every documented opt-in.
- `boom.php`: page, 404 and 500 per peer.
- `reporter-shape.php`: Host `localhost:8797`, which the allow-list admits, from a
  refused peer. That is the reporter's setup.

## Before and after (`out-3.13.148.txt`, PHP 8.4.26, Linux)

```
stock 4891b8d0, reporter shape
172.17.0.1   200 toolbar=1   404 toolbar=1   500 toolbar=2   /__dev/toolbar.js 403 non-loopback peer
fix (wip/fdev02)
127.0.0.1    200 toolbar=1   404 toolbar=1   500 toolbar=2   200
172.17.0.1   200 toolbar=0   404 toolbar=0   500 toolbar=0   403 non-loopback peer
```

The fix adds `DevAdmin::devSurfaceReachable()`: the Host allow-list plus the
loopback-peer-or-token gate. Injection, the overlay and `/__dev` now share it. The
same-origin check is left out on purpose, because a page render cannot answer it. The
overlay, when called directly without the router's verdict, judges the caller from the
server fields and fails closed.

A probe here once counted the bare string `tina4-dev-toolbar`. The overlay quotes
source lines, so it matched the probe's own code. The needle is now
`id="tina4-dev-toolbar"`.

## Other ports (3.13.148)

py, rb and nd are affected too (`python/`, `ruby/`, `nodejs/`; see the ledger row).
