#!/usr/bin/env python3
"""Generate the candidate patches for PY-FW-18 from the INSTALLED adapter.py.

Three of them, because the row's recommendation is that both halves are needed
and that claim should be re-runnable rather than asserted:

  a.patch   the dual-clock gate only          (compare on the driver's clock)
  b.patch   the strict driver option only     (floor(s)+1 instead of ceil(s))
  ab.patch  both

Generating them from the installed file rather than shipping fixed diffs means
they apply cleanly to whatever released version this project is pinned to, and
the script fails loudly if the source has moved instead of producing a patch
that silently changes nothing.

Usage:  .venv/bin/python tools/make-candidate-patches.py <outdir>
"""
import difflib
import os
import sys

REL = "tina4_python/database/adapter.py"

# ── the two halves, as exact-text substitutions ────────────────────────────
B_OLD = '''    """A driver's own connect-timeout option value, rounded UP to whole seconds.

    Every driver option here (libpq ``connect_timeout``, mysql-connector
    ``connection_timeout``, pymssql ``login_timeout``, pyodbc ``timeout``) is
    whole seconds. Rounding UP matters: a driver that fired EARLY \u2014 at 2s for a
    configured 2.5s \u2014 would raise its own raw error before our bound was
    reached, and the caller would see a bare driver message instead of one
    naming the variable that caused it.
    """
    return None if seconds is None else max(1, math.ceil(seconds))'''

B_NEW = '''    """A driver's own connect-timeout option, in whole seconds, STRICTLY longer
    than the bound it protects.

    Every driver option here (libpq ``connect_timeout``, mysql-connector
    ``connection_timeout``, pymssql ``login_timeout``, pyodbc ``timeout``) is
    whole seconds, so the bound has to become an integer \u2014 and which integer
    decides whether the driver's deadline lands after ours or on top of it.
    ``ceil`` put it on top: for a whole-second bound ``ceil(N) == N``, and the
    shipped default of 10 is whole. ``floor(s) + 1`` is strictly greater for
    every input, fractional or whole, which is what leaves the driver's own
    timer the room to fire first \u2014 the thing this wrapper is built on. The
    cost is at most one extra second, on a path that has already failed.
    """
    return None if seconds is None else max(1, math.floor(seconds) + 1)'''

A_OLD_INVARIANT = '''    The invariant that makes this work: the driver's option is always >= our
    bound (:func:`driver_connect_timeout_seconds` rounds UP), and our clock
    starts BEFORE the call, so the driver's own timeout cannot expire before
    ``elapsed`` has reached our bound. Break either half and a bare driver
    message reaches the caller instead of ours.'''

A_NEW_INVARIANT = '''    THE INVARIANT, AND WHY IT TAKES TWO CLOCKS
    ------------------------------------------
    What decides the race is not the driver's OPTION against our bound \u2014 it
    is the driver's ABORT INSTANT against our reading of a clock. Two things
    have to hold, and each of them was broken:

    * The driver's option must be STRICTLY greater than our bound, so its
      deadline lands after ours instead of on top of it.
      :func:`driver_connect_timeout_seconds` returns ``floor(s) + 1`` for that
      reason; ``ceil`` left a whole-second bound with no separation at all, and
      the default bound is a whole number.

    * The comparison has to be made on the clock the DRIVER used. libpq times
      ``connect_timeout`` with ``gettimeofday()`` \u2014 CLOCK_REALTIME \u2014 while a
      duration in Python belongs on ``time.monotonic()``. NTP slews and steps
      realtime and never touches monotonic, so a monotonic reading can still
      sit below the bound at the instant the driver has already given up, and
      then the driver's own message \u2014 which names no tunable \u2014 reaches
      the caller. :func:`bound_was_reached` compares both readings.

    Break either half and a bare driver message reaches the caller instead of
    ours.'''

A_ANCHOR = '''


@contextlib.contextmanager
def connect_deadline(host, port):'''

A_HELPER = '''


def bound_was_reached(elapsed_monotonic: float, elapsed_realtime: float,
                      seconds: float | None) -> bool:
    """Did a connect that failed take at least the configured bound?

    Two readings, because the framework and the driver do not share a clock.
    :func:`connect_deadline` times on ``time.monotonic()``; libpq times its own
    ``connect_timeout`` on ``gettimeofday()``. NTP moves the wall clock and
    never touches the monotonic one, so a forward step or slew can make the
    driver abort before a monotonic reading has reached the bound.

    Taking the LARGER of the two readings covers both directions: the realtime
    reading catches a forward jump, and keeping the monotonic reading means a
    BACKWARD jump cannot hide a timeout that really did happen.

    Pure, so the decision is testable without faking a clock.
    """
    if seconds is None:
        return False
    return max(elapsed_monotonic, elapsed_realtime) >= seconds


@contextlib.contextmanager
def connect_deadline(host, port):'''

A_OLD_STAMP = '''    seconds = resolve_connect_timeout()
    started = time.monotonic()
    try:
        yield seconds
    except Exception as failure:
        elapsed = time.monotonic() - started
        if seconds is not None and elapsed >= seconds:'''

A_NEW_STAMP = '''    seconds = resolve_connect_timeout()
    started = time.monotonic()
    started_realtime = time.time()
    try:
        yield seconds
    except Exception as failure:
        elapsed_monotonic = time.monotonic() - started
        elapsed_realtime = time.time() - started_realtime
        elapsed = max(elapsed_monotonic, elapsed_realtime)
        if bound_was_reached(elapsed_monotonic, elapsed_realtime, seconds):'''


def sub(text, old, new, label):
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly 1 occurrence, found {text.count(old)}")
    return text.replace(old, new)


def apply_b(text):
    return sub(text, B_OLD, B_NEW, "B docstring and body")


def apply_a(text):
    text = sub(text, A_OLD_INVARIANT, A_NEW_INVARIANT, "A invariant docstring")
    text = sub(text, A_OLD_STAMP, A_NEW_STAMP, "A clock stamps")
    # the helper lands immediately before connect_deadline, two blank lines each side
    return sub(text, A_ANCHOR, A_HELPER, "A helper insertion")


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    import tina4_python
    stock_path = os.path.join(os.path.dirname(tina4_python.__file__), "database", "adapter.py")
    with open(stock_path, encoding="utf-8") as fh:
        stock = fh.read()

    for name, fn in (("a", apply_a), ("b", apply_b),
                     ("ab", lambda t: apply_a(apply_b(t)))):
        fixed = fn(stock)
        if fixed == stock:
            raise SystemExit(f"{name}: produced no change")
        diff = difflib.unified_diff(
            stock.splitlines(keepends=True), fixed.splitlines(keepends=True),
            fromfile=f"a/{REL}", tofile=f"b/{REL}", n=3)
        out = os.path.join(outdir, f".fw18-candidate-{name}.patch")
        with open(out, "w", encoding="utf-8") as fh:
            fh.writelines(diff)
        print(f"wrote {out}  ({sum(1 for l in open(out)) } lines)")


if __name__ == "__main__":
    main()
