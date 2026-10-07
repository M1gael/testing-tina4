# `tina4 serve` kills a foreign process on its port

Ledger row `CLI-FW-02`. Run against tina4 CLI **3.8.88** release, source `origin/main`
`ac9dca2`, Linux.

## 2026-10-06 re-check (origin/main `598aebf`, built here as tina4 3.8.96)

`prove.sh` against that binary: foreign `-p`, foreign default, and a stale pid file all
die. A connected client is in `lsof -ti tcp:<port>` and dies with the server. SIGTERM of
the server alone leaves the client alive. `kill_port` is `src/console.rs:134`, called from
`src/main.rs:669` and `:693`. The stored patch does not apply (`src/main.rs`).

## Mechanism

When the port is busy, `src/main.rs:653` (`-p`) and `:677` (default port) call
`console::kill_port` (`src/console.rs:128`). It SIGTERMs every PID `lsof -ti tcp:<port>`
prints except its own. That output includes every connected client, not just the listener,
and nothing checks that any of them is a Tina4 server. Windows does the same with
`netstat | taskkill /F`.

All four frameworks already decided this (TAKEOVER-DEC-01). A dev server writes
`data/.tina4-serve-<port>.pid` when it binds, and takeover signals only that PID; a foreign
holder is refused. The Rust CLI never followed.

## Proof

```
./prove.sh                          # exit 1 on stock, 0 when the CLI follows the policy
BIN=<fixed binary> ./prove.sh
```

| case | stock 3.8.88 | fixed |
|---|---|---|
| foreign holder, `-p` | killed | survives, serve exits 1 naming the PID |
| foreign holder, default port | killed | survives |
| PID file naming another PID | killed | survives |
| own server (PID recorded), `-p` / default | reclaimed | reclaimed |

A client connected to the port was also killed on stock (run by hand; covered by
`a_connected_client_is_not_named_as_the_holder` in the fix's tests).

Real framework, fixed binary: tina4-python 3.13.136 started by `tina4 serve -p 8951`
records its listener PID. Once its supervisor was SIGKILLed, a second `tina4 serve -p 8951`
printed `Port 8951 freed (stopped Tina4 dev server, PID …)` and the new server recorded itself.

## Windows, 2026-10-06 (run)

Released 3.8.96 exe: the `cmd /C for /f` line does not parse, so nothing is killed
(`windows/out-3.8.96.txt`). This fix's `tina4.exe`, cross-built and run on the same
guest: a foreign holder, the default port, and a stale pid file are left running,
listener and client both alive. A pid file naming the listener stops that listener
and leaves the client alive (`windows/out-fix-598aebf.txt`).

## Not covered

- A non-English Windows `netstat` (the parser matches the word `LISTENING`).
- Opt-out (`--no-kill` / `TINA4_NO_TAKEOVER`), which the release notes promise, is `f-cli-26`.
- Another project's dev server on this port is refused, as the frameworks do: the PID file
  is project-local.
