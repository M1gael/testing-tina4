# Dev admin says "You are up to date!" when it could not reach the registry

The dev toolbar's version check answers **HTTP 200 with `latest == current`** whenever the
call to the package registry fails. The browser cannot tell that apart from a real answer, so
a developer several releases behind, on a machine with no route out, is shown a green
**"Latest: v3.13.125 — You are up to date!"**

The toolbar already has the correct UI for this case. It is unreachable.

**Present in four ports.** Python, PHP, Ruby and Node.js each carry the same handler, down to
the same comment (`// Offline or timeout — return current as latest`).

Versions: tina4 CLI **3.8.77**; frameworks pinned at **3.13.125** for the run, latest on every
registry **3.13.131**, 2026-09-03.

## Mechanism

Every port wraps the registry call in a catch-all and, on failure, leaves `latest` at the
value it was initialised to — which is `current`:

| Port | `file:line` | Failure path |
|---|---|---|
| python | `tina4_python/dev_admin/__init__.py:2172` `_api_version_check` | `except Exception: pass` |
| php | `Tina4/DevAdmin.php:409` version-check route | `catch (\Throwable)`, plus `@file_get_contents` |
| ruby | `lib/tina4/dev_admin.rb:787` `version_check_payload` | `rescue StandardError`, and a non-2xx response falls through the same way |
| nodejs | `packages/core/src/devAdmin.ts:2087` `handleVersionCheck` | `catch {}`, and `if (resp.ok)` skips silently |

The response is then `{"current": X, "latest": X}` with status 200.

The client half, python at `__init__.py:2376`, branches on exactly that:

```js
if (latest === current) { upToDate(el, latest); return; }
...
}).catch(function () {
    el.className = 't4-err';
    el.textContent = 'Could not check for updates (offline?)';
});
```

`upToDate()` at `:2366` writes *"You are up to date!"* in green. The `.catch` branch is the
right message and can never run: the server turned the failure into a 200.

**A failure is being reported as a definite, benign conclusion** — the same shape as
`f-cli-05`, where a local disk write failure was reported as "no build for your platform".

## Reproduction

`./prove.sh` — scaffolds a python project, pins the framework at a release that is
deliberately old, and asks the endpoint twice.

```
== framework pinned at 3.13.125 (deliberately behind latest)
== asking with the network up
   {"current":"3.13.125","latest":"3.13.131"}      <- correct: update available
== asking with the registry unreachable (https_proxy to a dead port)
   {"current":"3.13.125","latest":"3.13.125"}      <- "You are up to date!"
```

Exit 1 means reproduced. Exit 2 means the pinned version happens to be the latest, so the run
proves nothing — pick an older `OLD_VERSION`.

## How the other three were checked

PHP, Ruby and Node.js do not honour `https_proxy`, so they were run inside an isolated network
namespace instead — `unshare -rn`, loopback only, no route out (confirmed: `curl https://pypi.org`
exits 7 inside it). All three answered:

```
{"current":"3.13.131","latest":"3.13.131"}   HTTP=200
```

Node.js was then pinned back to `tina4-nodejs@3.13.125` and run both ways, which is decisive on
its own:

```
ONLINE   {"current":"3.13.125","latest":"3.13.131"}
OFFLINE  {"current":"3.13.125","latest":"3.13.125"}
```

For PHP and Ruby the offline 200 was observed but not the outdated-version variant; their
failure paths were read at the lines above.

## Not affected

- **tina4js** — a browser library, no dev-admin server.
- **delphi** — no dev admin and no `/__dev` routes at all.
- **the Rust CLI** — its version check is `tina4 update`, a different code path with its own
  defects recorded as `f-cli-05`, `f-cli-06` and `f-cli-08`.

## Shape of a fix

The client is already correct, so the server should stop lying to it: return the failure
(a non-200, or `latest: null` with a reason) and let the existing `.catch` branch — or a small
addition beside it — say *"Could not check for updates"*. Four ports, four small changes, one
behaviour. Nothing else in the endpoint needs to move.
