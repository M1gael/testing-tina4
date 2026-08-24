#!/usr/bin/env python3
"""Apply or revert the candidate fix on the installed released bundle."""
import hashlib, io, sys

DIST = "node_modules/tina4-nodejs/packages/core/dist/index.js"
STOCK_MD5 = "2e405d40e57a320c89d4d9b6cc38199e"

BEFORE = """      static stop(name) {
        const targets = name ? [registry.get(name)].filter(Boolean) : Array.from(registry.values());
        for (const svc of targets) {
          svc.context.running = false;
"""

AFTER = """      static stop(name) {
        const targets = name ? [registry.get(name)].filter(Boolean) : Array.from(registry.values());
        for (const svc of targets) {
          const instance = svc.instance;
          if (instance && typeof instance.stop === "function") {
            try {
              instance.stop();
            } catch {
            }
          }
          svc.context.running = false;
"""


def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


mode = sys.argv[1]
src = io.open(DIST, encoding="utf-8").read()

if mode == "apply":
    if md5(DIST) != STOCK_MD5:
        sys.exit(f"refusing to patch: {DIST} is not the stock 3.13.114 bundle")
    if src.count(BEFORE) != 1:
        sys.exit("refusing to patch: stop() does not match the expected stock text")
    io.open(DIST, "w", encoding="utf-8").write(src.replace(BEFORE, AFTER))
    print("patched")
elif mode == "revert":
    io.open(DIST, "w", encoding="utf-8").write(src.replace(AFTER, BEFORE))
    got = md5(DIST)
    print(f"restored, md5 {got} {'OK' if got == STOCK_MD5 else 'MISMATCH — REINSTALL'}")
    sys.exit(0 if got == STOCK_MD5 else 1)
elif mode == "verify":
    got = md5(DIST)
    print(f"md5 {got} {'stock' if got == STOCK_MD5 else 'NOT STOCK'}")
    sys.exit(0 if got == STOCK_MD5 else 1)
