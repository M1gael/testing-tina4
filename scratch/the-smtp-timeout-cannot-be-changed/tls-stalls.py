#!/usr/bin/env python3
"""Two SMTP relays that stall DURING TLS: the cells the plain-text tests never reach.

  implicit   accepts TCP, says nothing  -> the client's ssl:// handshake never gets a ServerHello
  starttls   220 greeting, EHLO answered with STARTTLS, "220 go", then silence -> handshake stalls
             AFTER the plain-text part of the session

Prints "<implicit-port> <starttls-port>" then serves.
"""
import socket, threading

def listener():
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0)); s.listen(16); return s

held = []
def implicit(s):
    while True:
        c, _ = s.accept(); held.append(c)

def starttls(s):
    while True:
        c, _ = s.accept(); held.append(c)
        threading.Thread(target=serve, args=(c,), daemon=True).start()

def serve(c):
    f = c.makefile("rwb", buffering=0)
    f.write(b"220 stall.example ESMTP\r\n")
    while True:
        line = f.readline()
        if not line: return
        cmd = line.strip().upper()
        if cmd.startswith(b"EHLO") or cmd.startswith(b"HELO"):
            f.write(b"250-stall.example\r\n250 STARTTLS\r\n")
        elif cmd == b"STARTTLS":
            f.write(b"220 go ahead\r\n")
            return            # now silent: the client's handshake waits for a ServerHello

a, b = listener(), listener()
print(a.getsockname()[1], b.getsockname()[1], flush=True)
threading.Thread(target=implicit, args=(a,), daemon=True).start()
starttls(b)
