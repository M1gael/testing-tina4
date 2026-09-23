# `tina4 serve` kills a foreign process on its port

Ledger row `CLI-FW-02`. Run against tina4 CLI **3.8.88** release, source `origin/main`
`ac9dca2`, Linux.

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

## Not covered

- Windows is read, not run. The netstat parser is tested only against a hand-written sample.
- Opt-out (`--no-kill` / `TINA4_NO_TAKEOVER`), which the release notes promise, is `f-cli-26`.
- Another project's dev server on this port is refused, as the frameworks do: the PID file
  is project-local.
