#!/usr/bin/env python3
"""A listener whose accept queue is full: the next client's SYN is dropped, so
its connect() hangs in the kernel's SYN retries. Prints its port, then holds."""
import socket, time
s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(0)
port = s.getsockname()[1]
fill = []
for _ in range(4):                       # fill the queue; never accept()
    c = socket.socket(); c.setblocking(False)
    try: c.connect(("127.0.0.1", port))
    except BlockingIOError: pass
    fill.append(c)
time.sleep(0.5)
print(port, flush=True)
while True: time.sleep(60)
