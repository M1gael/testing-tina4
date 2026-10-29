#!/usr/bin/env python3
"""Run a command under a pty and answer prompts only when they appear.

usage: drive.py <log> <timeout-seconds> <prompt=answer>... -- <command...>
Each prompt=answer pair is used once, in order; the prompt is matched as plain
text in the output seen since the previous answer. Exit status is the command's.
"""
import os, pty, select, sys, time

args = sys.argv[1:]
log, timeout = args[0], float(args[1])
sep = args.index("--")
pairs = [a.split("=", 1) for a in args[2:sep]]
cmd = args[sep + 1:]

pid, fd = pty.fork()
if pid == 0:
    os.execvp(cmd[0], cmd)

seen = b""
deadline = time.time() + timeout
with open(log, "wb") as out:
    while True:
        if time.time() > deadline:
            out.write(b"\n[drive.py] TIMEOUT\n")
            os.kill(pid, 9)
            break
        r, _, _ = select.select([fd], [], [], 1)
        if fd in r:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            out.write(data); out.flush()
            seen += data
            if pairs and pairs[0][0].encode() in seen:
                time.sleep(0.3)
                os.write(fd, pairs[0][1].encode() + b"\r")
                pairs.pop(0)
                seen = b""
_, status = os.waitpid(pid, 0)
sys.exit(os.waitstatus_to_exitcode(status))
