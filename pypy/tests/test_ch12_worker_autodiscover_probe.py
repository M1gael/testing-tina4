# Probe — covers PY-12-09. Proves the S12 worker at the documented path
# `src/workers/email_worker.py` hangs `tina4 serve`: Tina4 auto-discovers every
# `src/**/*.py` at startup and imports it, but importing the worker module runs
# its top-level infinite `consume()` loop, which never returns.
#
# Doc under test : documentation/tina4-book/book-1-python/chapters/12-queues.md (S12, lines 552-583)
# Framework      : tina4_python.core.server._auto_discover (READ-ONLY — never modified)
import os
import sys
import subprocess
import tempfile

import pytest

DOC = "documentation/tina4-book/book-1-python/chapters/12-queues.md"

# Mirror of server.py _auto_discover's filter (lines 92/109/111): a file is
# imported unless a path part is in this skip set or starts with "_".
_AUTODISCOVER_SKIP = {"public", "templates", "scss", "locales", "icons"}


def test_documented_worker_path_is_not_skipped_by_autodiscover():
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S12 Solution): "Create a separate consumer file `src/workers/email_worker.py`".

    The documented path lives under src/ and is neither in the auto-discover skip
    set nor `_`-prefixed, so `_auto_discover("src")` WOULD import it at boot.
    """
    rel_parts = ("workers", "email_worker.py")  # parts of src/workers/email_worker.py under src/
    assert not any(p in _AUTODISCOVER_SKIP for p in rel_parts), (
        "src/workers is not a skipped sub-tree"
    )
    assert not any(p.startswith("_") for p in rel_parts), (
        "the documented filename is not underscore-prefixed (would be skipped)"
    )
    # => auto-discover imports it; the next test proves importing it blocks.


def test_importing_the_worker_module_blocks_forever():
    """documentation/tina4-book/book-1-python/chapters/12-queues.md
    (S12 Solution, worker): the top-level `for job in queue.consume("emails"):`
    loop "runs forever" (S4). Importing the module therefore never returns —
    which is exactly what `_auto_discover` does at server startup.

    PY-12-09: import the verbatim worker module in a subprocess against an EMPTY
    queue with a hard timeout. consume() sleeps-when-empty and never yields, so
    the import never completes → the subprocess times out (proof of the boot hang).
    """
    empty_q = tempfile.mkdtemp(prefix="ch12_py1209_")
    env = dict(os.environ)
    env["TINA4_QUEUE_PATH"] = empty_q          # empty -> consume() sleeps forever
    env.pop("TINA4_QUEUE_BACKEND", None)        # file backend
    # Importing src.workers._email_worker runs its top-level consume loop. The
    # module body is byte-identical to the documented src/workers/email_worker.py
    # (only the filename differs — see that file's header / PY-12-09).
    code = "import importlib; importlib.import_module('src.workers._email_worker')"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=os.getcwd(), env=env,
            capture_output=True, timeout=6,
        )
    except subprocess.TimeoutExpired:
        return  # expected: the import never returned -> server boot would hang
    pytest.fail(
        f"importing the worker returned (rc={proc.returncode}) — expected it to "
        f"block forever. stderr: {proc.stderr.decode(errors='replace')[:400]}"
    )
