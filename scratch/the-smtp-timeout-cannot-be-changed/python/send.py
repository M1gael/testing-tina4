"""One Messenger.send() against the port given in argv[1]; prints the outcome and the wait.

argv[2] picks the lever under test: "plain", "ctor" (timeout=2 to the constructor),
or "socketdefault" (socket.setdefaulttimeout(2) first). TINA4_MAIL_TIMEOUT comes
from the environment, if the caller sets it.
"""
import socket, sys, time

from tina4_python.messenger import Messenger

port, lever = int(sys.argv[1]), sys.argv[2]
kwargs = dict(host="127.0.0.1", port=port, from_address="app@localhost", encryption="none")
if lever == "socketdefault":
    socket.setdefaulttimeout(2)
start = time.monotonic()
try:
    if lever == "ctor":
        kwargs["timeout"] = 2
    result = Messenger(**kwargs).send("someone@localhost", "test", "hello")
    outcome = f"success={result['success']} message={result['message']!r}"
except Exception as exc:
    outcome = f"raised {type(exc).__name__}: {exc}"
print(f"{outcome} after {time.monotonic() - start:.1f} s")
