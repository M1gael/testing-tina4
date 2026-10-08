#!/usr/bin/env python3
"""Accepts TCP connections on a free port, closes each at once, and counts them.
Prints the port, then the running count on stdout after each connection."""
import socket
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 0)); s.listen(16); print(s.getsockname()[1], flush=True)
n = 0
while True:
    c, _ = s.accept(); n += 1; c.close(); print(n, flush=True)
