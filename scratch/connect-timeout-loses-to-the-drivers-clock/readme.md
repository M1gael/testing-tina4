# The framework's connect-timeout message loses a race to the driver's own

Ledger row: [`PY-FW-18`](../../known-issues/ledger.md)

## Overview

`TINA4_DATABASE_CONNECT_TIMEOUT` exists so that a database connect which blocks
forever surfaces as an error naming the variable an operator can tune. For the two
adapters that lean on the driver's own timer — PostgreSQL and MySQL — the framework
does not run a competing countdown. It lets the driver abort at its own deadline and
then **translates** that failure into `DatabaseConnectTimeout`, keeping the driver's
error as `__cause__`. `connect_deadline`'s docstring is explicit that this is a
translator, not a second timer, and that the translation cannot be missed.

It can be missed. The framework decides whether to translate by comparing a
`time.monotonic()` reading against the bound, while libpq measures its own
`connect_timeout` on `gettimeofday()`. Those are two different clocks, NTP moves
one and never the other, and when they disagree the driver aborts before the
framework's reading has reached the bound. The gate declines, and the caller gets
libpq's `timeout expired` — which names nothing an operator can act on.

## Environment and versions

- **tina4-python**: `3.13.107` (released, installed from PyPI — not a working copy)
- **psycopg2-binary**: `2.9.12`, statically bundled **libpq `170009`**
- **Date**: 2026-08-21
- **Stock MD5 (`database/adapter.py`)**: `695ed6b2b98c8f66ab1ff502af9e9024`
- `adapter.py` and `postgres.py` as installed were verified byte-identical to
  upstream `v3` on the day of measurement, so this is not a stale copy.
- **Environment status**: `.venv` is left unpatched. `prove.sh --fixed` restores it
  on an `EXIT` trap and verifies the restore against the stock MD5 above.

## Root cause

### 1. The two clocks

`tina4_python/database/adapter.py:114-127` — `connect_deadline` stamps and compares
on `CLOCK_MONOTONIC`:

```python
    seconds = resolve_connect_timeout()
    started = time.monotonic()
    try:
        yield seconds
    except Exception as failure:
        elapsed = time.monotonic() - started
        if seconds is not None and elapsed >= seconds:
            raise DatabaseConnectTimeout(...) from failure
        raise
```

libpq measures its own deadline on `CLOCK_REALTIME`. Straight out of the driver
binary, no inference required:

```
$ nm -D --undefined-only .venv/.../psycopg2/_psycopg.cpython-313-x86_64-linux-gnu.so
                 U gettimeofday@GLIBC_2.2.5
```

`gettimeofday` is `CLOCK_REALTIME`, and there is no `clock_gettime` import at all —
nothing in libpq reads the clock the framework is using. NTP slews and steps
realtime continuously and never touches monotonic.

### 2. And no separation to absorb it

`adapter.py:64-74` rounds the driver's option **up**:

```python
    return None if seconds is None else max(1, math.ceil(seconds))
```

For any whole-second bound `ceil(N) == N`, so the driver's deadline and the
framework's land on the same instant. `DEFAULT_CONNECT_TIMEOUT_SECONDS = 10.0`
(`adapter.py:26`) is whole, so the default deployment is the affected case. The only
thing normally holding `elapsed` above the bound is that `started` is stamped a few
hundred microseconds before libpq starts its own clock.

### 3. The docstring states the invariant, and states it wrongly

`adapter.py:109-112`:

> the driver's option is always >= our bound (`driver_connect_timeout_seconds`
> rounds UP), and our clock starts BEFORE the call, so the driver's own timeout
> cannot expire before `elapsed` has reached our bound.

What decides the race is not the driver's *option* against the bound — it is the
driver's *abort instant* against our *reading of a clock*. `>=` is not `>`, and the
two readings are not on the same clock.

## Reproduction

Two real conditions, no mocks and no monkeypatching anywhere in this project:

1. **A server that answers one byte and then stalls.** `prove.py`'s `dribble` mode
   completes libpq's SSL negotiation, reads the StartupMessage, waits, then sends a
   single byte of a message it never finishes. That byte forces libpq to poll a
   second time and **recompute its remaining budget from realtime**.
2. **Realtime running ahead of monotonic.** `skew.so` (`LD_PRELOAD`) intercepts
   `gettimeofday`, `clock_gettime` and `time`, skewing only `CLOCK_REALTIME` by
   `SKEW_RATE`. This is what NTP does, on demand.

```bash
./prove.sh                # stock released framework
./prove.sh --fixed        # candidate A+B
./prove.sh --fixed a      # dual-clock gate only
./prove.sh --fixed b      # strict driver option only
```

### How wide the window is

On a **silent** wedged server — the case that fails in upstream CI — libpq reads
realtime 5 times, 4 of them inside the first **52 microseconds**, then once when
`poll()` returns at 2001 ms. The last read before the wait is where the remaining
budget becomes a *relative* `poll()` timeout, and the kernel measures that on
monotonic. So a forward realtime jump only shortens the wait if it lands inside
that ~52 µs window: rare per connect, which matches an intermittent CI failure, and
not on its own a full account of the observed rate.

## Before and after

Bound 2 s throughout. Full output in [`evidence/`](evidence/).

| candidate | 1.0x, silent | 1.0x, dribble | 1.3x | 2.0x | wait on the failure path |
|---|---|---|---|---|---|
| **stock** | holds 2.0162 s | holds 2.0151 s | **BREAKS** 1.5641 s | **BREAKS** 1.5157 s | 2.0 s |
| **A** dual-clock gate | holds 2.0157 s | holds 2.0160 s | holds 1.5638 s | holds 1.5158 s | 2.0 s |
| **B** `floor(s)+1` | holds 3.0161 s | holds 3.0169 s | holds 2.5652 s | **BREAKS** 1.5165 s | 3.0 s |
| **A+B** | holds 3.0159 s | holds 3.0167 s | holds 2.5651 s | holds 1.5161 s | 3.0 s |

*holds* = `DatabaseConnectTimeout`, whose message names the variable.
*BREAKS* = `psycopg2.OperationalError: ... timeout expired`, which names nothing.

**A is what closes the defect**, and it costs no extra waiting — the driver still
aborts at its own deadline. **B closes nothing that A does not**, and it adds a
second to every failed connect (a 2 s bound waits 3 s; the shipped 10 s default
waits 11 s). B earns its place for a different reason: it stops the correctness of
the message depending on the gate at all, for any driver that fires early for
reasons other than clock divergence — mysql-connector, pymssql and pyodbc each run
their own timer, and only libpq's was measured here.

## The candidate

`tools/make-candidate-patches.py` generates all three patches from the *installed*
`adapter.py`, so they apply to whatever version this project is pinned to and fail
loudly rather than silently changing nothing. The substance:

- `driver_connect_timeout_seconds` returns `max(1, math.floor(seconds) + 1)` —
  strictly greater than the bound for every input, whole or fractional.
- a pure `bound_was_reached(elapsed_monotonic, elapsed_realtime, seconds)` takes the
  larger of the two readings, so the realtime reading catches a forward jump while
  keeping the monotonic one means a backward jump cannot hide a real timeout. Pure,
  so the decision is testable without faking a clock.
- the invariant paragraph in `connect_deadline`'s docstring is rewritten to say what
  actually has to hold.

Both existing pinned assertions survive unchanged:
`test_driver_option_is_never_shorter_than_the_configured_bound` asserts only
`option >= configured`, and `test_fractional_bound_is_rounded_up_for_whole_second_driver_options`
pins `2.5 -> 3` and `0.2 -> 1`, which `floor(s)+1` also gives.
