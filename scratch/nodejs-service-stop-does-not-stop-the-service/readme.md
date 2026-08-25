# nodejs-service-stop-does-not-stop-the-service

Proof project for **`f-svc-01`** in **tina4-nodejs** — the Node port of the defect fixed in
Python by [#118](https://github.com/tina4stack/tina4-python/pull/118).

**`ServiceRunner.stop()` does not stop a class-based `Tina4Service`.** The runner reports the
service as stopped and returns immediately; the service's `run()` loop keeps going for the
lifetime of the process.

Proven against **released `tina4-nodejs@3.13.114`** installed from npm — not against a checkout.

```bash
./prove.sh     # exit 0 = reproduced on stock AND closed by the candidate fix
```

`prove.sh` runs `repro.mjs` twice against the *installed* bundle: once stock, once with the
candidate fix applied by `patch.py`. It restores the bundle afterwards and verifies the md5
against the stock hash, so the installed package is never left patched.

## What it does

Registers the same workload twice, each written the way the framework documents its own pattern:

| service | registered with | exit condition it loops on |
|---|---|---|
| `class_service` | `ServiceRunner.registerService(name, new CountingService())` | `this.shouldStop()` — the loop from the `Tina4Service` docstring |
| `plain_service` | `ServiceRunner.register(name, async (ctx) => ...)` | `ctx.running` |

Both start, run ~300 ms, then `ServiceRunner.stop()` is called. Each service's loop counter is
sampled at `stop()` and again 300 ms later. A service that stopped has a delta of 0.

## Stock — the defect

```
tina4-nodejs 3.13.114  (released, from npm)
stop() returned in 0.2359 ms

service        loops at stop()   loops 300ms later   delta   run() exited   isRunning()
class_service               59                 116      57          false   false
plain_service               58                  58       0           true   false

FAIL  stop() did not stop the class-based service:
      it ran 57 more loops after stop() returned, and run() has not exited.
```

The plain-callable control is the point of the experiment: it stops correctly, so the
`ctx.running` path works and only the class-based path is broken.

Note `isRunning("class_service")` returning **`false` while the loop is still counting**. The
runner does not merely fail to stop the service — it reports it as stopped.

## With the candidate fix

```
stop() returned in 0.3906 ms

service        loops at stop()   loops 300ms later   delta   run() exited   isRunning()
class_service               58                  58       0           true   false
plain_service               57                  57       0           true   false

PASS  stop() stopped the class-based service.
```

## Mechanism

All line numbers are `packages/core/src/service.ts` at 3.13.114.

1. `registerService()` stashes the instance on the registry entry at **:273**, under a comment
   reading *"Stash the instance on the registry entry so future stop() calls can route to
   service.stop()"*. The word *future* is an accurate description of code that was never written.
2. `ServiceRunner.stop()` (**:359-372**) sets `svc.context.running = false` and clears the
   interval timer. It never reads `instance`. Grepping the whole file for `instance` returns
   exactly two hits — the comment at :269 and the write at :273. **Written once, read nowhere**,
   which is the same test that characterised the Python defect.
3. `Tina4Service._running` (**:186**) is cleared only by `Tina4Service.stop()` (**:195-197**),
   and `shouldStop()` (**:207-209**) reads it. With nothing calling `stop()`, `shouldStop()`
   never returns true and the documented `while (!this.shouldStop())` loop never exits.
4. **The class-based service cannot fall back on `context.running` either.** `executeHandler`
   passes the context to the handler at **:114** (`await svc.handler(svc.context)`), but
   `asHandler()` (**:215-219**) returns `async () => { await this.run(); }` — it discards the
   argument. So the context the runner does update is not reachable from inside `run()`.
5. Daemon services run their handler exactly once (`startDaemonService`, **:159-162**) and the
   handler owns its loop, so there is nothing else that could end it.

Unlike Python there is no thread and no 5 s join to stall on, so the symptom differs: `stop()`
returns in a quarter of a millisecond and the loop simply outlives it.

## The fix

```ts
for (const svc of targets) {
  const instance = svc.instance;
  if (instance && typeof instance.stop === "function") {
    try {
      instance.stop();
    } catch (err) {
      Log.error("Error stopping service instance", { name: svc.name, error: ... });
    }
  }
  svc.context.running = false;
  ...
```

Plus `instance?: Tina4Service` on the `RegisteredService` interface, which lets `registerService`
drop its `as unknown as Record<string, unknown>` cast. The `try`/`catch` matters: one service
whose `stop()` throws must not prevent the rest from stopping — there is a regression test for
exactly that.

**Landed upstream.** Branch `fix/service-runner-stop-ignores-instance` @ `83ac514` in
`gitdir/tinaforks/tina4-nodejs`, filed as
[#58](https://github.com/tina4stack/tina4-nodejs/pull/58) (+138/-3), merged into `v3` on
2026-08-24 as `ead390c` with zero reviews, released in **3.13.116**.

Because the fix ships from 3.13.116, this project is pinned to 3.13.114 by `package-lock.json`.
Reinstalling without the lock file will pull a fixed version and the reproduction will report a
false pass.

## Still open

`f-svc-01` remains **affected** in **php** (`Tina4/ServiceRunner.php`) and **ruby**
(`lib/tina4/service_runner.rb`), by source read. Neither has been reproduced by execution —
no php or ruby toolchain is installed on this machine.
