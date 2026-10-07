#!/usr/bin/env python3
"""A relay that dribbles its greeting one byte per second: every read succeeds inside the
per-read bound, so a per-operation timeout never fires. Prints its port, serves one client."""
import socket, time, threading
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 0)); s.listen(4); print(s.getsockname()[1], flush=True)
def go(c):
    try:
        for b in b"220 drip.example ESMTP ready\r\n":
            c.send(bytes([b])); time.sleep(1)
        time.sleep(60)
    except Exception: pass
while True:
    c, _ = s.accept(); threading.Thread(target=go, args=(c,), daemon=True).start()
