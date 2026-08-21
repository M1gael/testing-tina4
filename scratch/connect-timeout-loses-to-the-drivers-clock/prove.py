#!/usr/bin/env python3
"""One probe of PY-FW-18. prove.sh runs this repeatedly under different clocks.

    prove.py silent      wedged server that never writes a byte  (the CI case)
    prove.py dribble     wedged server that answers one byte and then stalls
    prove.py exposure    measure how wide the window actually is

The bound comes from TINA4_DATABASE_CONNECT_TIMEOUT; the clock divergence comes
from SKEW_RATE, applied by skew.so via LD_PRELOAD.

What a probe asserts: which exception class reaches the caller. The framework
promises DatabaseConnectTimeout, whose message names the variable an operator
would tune. psycopg2.OperationalError reaching the caller means the promise was
broken -- the operator gets libpq's "timeout expired", which names nothing.
"""
import os
import socket
import sys
import threading
import time

# quiet the framework's own startup logging so the probe output is the output
os.environ.setdefault("TINA4_DEBUG", "false")
os.environ.setdefault("TINA4_LOG_LEVEL", "ERROR")

MODE = sys.argv[1] if len(sys.argv) > 1 else "silent"
# The bound has to be in os.environ before the framework resolves it -- a whole
# number, which is the affected case and what the shipped default also is.
os.environ.setdefault("TINA4_DATABASE_CONNECT_TIMEOUT", "2")
RATE = os.environ.get("SKEW_RATE", "1.0")

from tina4_python.database.adapter import (          # noqa: E402
    DatabaseConnectTimeout, resolve_connect_timeout,
)
from tina4_python.database.postgres import PostgreSQLAdapter  # noqa: E402

# Ask the framework what it resolved rather than trusting our own reading of it.
BOUND = resolve_connect_timeout()
DRIBBLE_AT = BOUND * 0.75


def wedged_server(mode):
    """A real listening socket. No mocks anywhere in this project."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(64)
    held = []

    def one_client(conn):
        held.append(conn)
        if mode == "silent":
            time.sleep(30)          # accept, and never write anything
            return
        accepted = time.monotonic()
        conn.settimeout(0.5)
        try:
            conn.recv(8)            # libpq's 8-byte SSLRequest
            conn.sendall(b"N")      # decline SSL, stay on the plain protocol
            conn.recv(4096)         # the StartupMessage
        except OSError:
            return
        time.sleep(max(0.0, DRIBBLE_AT - (time.monotonic() - accepted)))
        try:
            conn.sendall(b"R")      # 1 of the 5 bytes of an auth-request header
        except OSError:
            return
        time.sleep(30)              # and then nothing, ever

    def accept_forever():
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            threading.Thread(target=one_client, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_forever, daemon=True).start()
    return srv.getsockname()


def probe(mode):
    host, port = wedged_server(mode)
    started = time.monotonic()
    try:
        PostgreSQLAdapter().connect(f"postgresql://u:p@{host}:{port}/d")
        outcome, detail = "CONNECTED", "the wedged server should never accept a login"
    except DatabaseConnectTimeout as exc:
        outcome, detail = "DatabaseConnectTimeout", str(exc).splitlines()[0]
    except Exception as exc:
        outcome = f"{type(exc).__module__}.{type(exc).__name__}"
        detail = str(exc).strip().splitlines()[-1]
    elapsed = time.monotonic() - started

    kept = outcome == "DatabaseConnectTimeout"
    print(f"  server={mode:<8} SKEW_RATE={RATE:<5} bound={BOUND:g}s  "
          f"monotonic elapsed={elapsed:7.4f}s   "
          f"{'PROMISE KEPT ' if kept else 'PROMISE BROKEN'}  {outcome}")
    print(f"      {detail}")
    return kept


def exposure():
    """How wide is the window in which a realtime jump can shorten libpq's wait?

    Python reads the clock through clock_gettime, so every gettimeofday call in
    the process is libpq's. The first is where it computes its deadline; the
    last before the long wait is where it converts what remains into a relative
    poll() timeout, which the kernel then measures on MONOTONIC. Only a jump
    landing BETWEEN those two can shorten the wait.
    """
    log = os.environ.get("SKEW_LOG")
    if not log:
        print("  exposure: needs SKEW_LOG set (prove.sh does this)")
        return True
    probe("silent")
    stamps = [int(x) for x in open(log) if x.strip()]
    if len(stamps) < 2:
        print(f"      only {len(stamps)} realtime reads seen -- nothing to measure")
        return True
    # The long poll is the biggest gap between consecutive reads. Everything
    # before it is libpq setting its deadline and then converting what remains
    # into a relative poll() timeout; everything after is the post-poll check.
    gaps = [stamps[i + 1] - stamps[i] for i in range(len(stamps) - 1)]
    k = gaps.index(max(gaps))
    cluster, base = stamps[: k + 1], stamps[0]
    print(f"      libpq read the realtime clock {len(stamps)} times; "
          f"{len(cluster)} before the long wait:")
    prev = None
    for t in cluster:
        gap = "" if prev is None else f"   (+{(t - prev) / 1e6:.4f} ms)"
        print(f"        t = {(t - base) / 1e6:10.4f} ms{gap}")
        prev = t
    print(f"        t = {(stamps[k + 1] - base) / 1e6:10.4f} ms"
          f"   (+{max(gaps) / 1e6:.4f} ms)   <- poll() returned; wait is over")
    print(f"      exposure window = {(cluster[-1] - cluster[0]) / 1e6:.4f} ms. "
          f"A forward realtime jump only shortens the wait if it lands in there,")
    print(f"      because the last read is where the remaining budget becomes a "
          f"relative poll() timeout -- and the kernel measures THAT on monotonic.")
    return True


sys.exit(0 if (exposure() if MODE == "exposure" else probe(MODE)) else 1)
