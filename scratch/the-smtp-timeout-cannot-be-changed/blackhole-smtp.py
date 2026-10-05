#!/usr/bin/env python3
"""An SMTP port that accepts the TCP connection and then says nothing, ever.

This is the wedged-relay shape: the connect succeeds, so no connect timeout
applies; the client blocks reading a greeting that never comes, and only the
socket read timeout ends it. Prints the bound port on stdout, then serves.
"""
import socket, sys, threading

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 0))
s.listen(16)
print(s.getsockname()[1], flush=True)
held = []
while True:
    conn, _ = s.accept()
    held.append(conn)          # never read, never write, never close
