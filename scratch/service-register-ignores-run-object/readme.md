# Investigation: ServiceRunner.register Ignores Plain Objects with run()

## Summary

`ServiceRunner.register(name, handler)` silently accepts plain class instances that define a `run()` method but never executes their `run()` logic. In stock `tina4-python 3.13.107`, `_run_service` expects `svc["handler"]` to be callable with `(ctx)`, causing non-callable plain class instances to raise `TypeError: '<ClassName>' object is not callable` in background worker threads until max retries are exhausted. Additionally, `ServiceRunner.stop()` fails to call `instance.stop()` on registered service instances.

## Environment & Versions

- **tina4-python**: `3.13.107`
- **tina4 CLI**: `3.8.77`
- **Python**: `3.13`
- **Date**: 2026-08-20
- **Stock MD5 (`service/__init__.py`)**: `332d3e38acdbc418d3b19994c6e43e5c`

## Broken Published Contract

The official documentation in `docs/python/27-service-runner.md` explicitly teaches registering plain class instances implementing `run()` and `stop()`:

- **Line 13**: *"A service is any class with a `run()` method. Start it with the runner and it executes in the background:"*
- **Lines 19–37 (specifically Line 35)**:
  ```python
  class HeartbeatService:
      def __init__(self, interval=30):
          self.interval = interval
          self.running = False

      def run(self):
          self.running = True
          while self.running:
              print(f"Heartbeat at {time.strftime('%H:%M:%S')}")
              time.sleep(self.interval)

      def stop(self):
          self.running = False


  runner = ServiceRunner()
  runner.register("heartbeat", HeartbeatService(interval=30))
  runner.start()
  ```
  Similar patterns appear at lines 136 (`runner.register("email_worker", EmailWorker())`), 189 (`runner.register("cache_warmer", ScheduledTask(...))`), 203–206, and 364 (`runner.register("product_cache_warmer", ProductCacheWarmer(interval=60))`). None of these classes inherit from `Service`.
- **Line 224**: *"`stop()` calls `stop()` on each registered service and waits for their threads to finish."*

## Mechanism Analysis

In `.venv/lib/python3.13/site-packages/tina4_python/service/__init__.py`:

1. **Registration without runtime type validation (`service/__init__.py:264-288`)**:
   `register(self, name: str, handler: callable, interval: int = 60, cron: str = None, daemon: bool = False, max_retries: int = 3)` takes `handler` and unconditionally appends it to `self.services` as `{"name": name, "handler": handler, ...}`. The Python type annotation `handler: callable` is not enforced at runtime. Non-callable objects (and nonsensical values like `42` or `object()`) are silently stored without raising an error.

2. **Handler invocation in worker threads (`service/__init__.py:532, 541, 550`)**:
   When `ServiceRunner.start()` spawns worker threads running `_run_service(self, svc, ctx)`, line 550 (or line 532 for daemon mode) executes `svc["handler"](ctx)`. Because a plain class instance does not implement `__call__`, Python raises `TypeError: '<ClassName>' object is not callable`.

3. **Silent failure loop (`service/__init__.py:557-575`)**:
   The exception is caught by `except Exception as exc:` in `_run_service`. It increments `retries`, logs a `"Service error"`, backs off, retries 3 times, and finally logs `"Service max retries exceeded, stopping"` before exiting the thread. The service's `run()` method is never invoked (0 invocations).

4. **Missing `stop()` dispatch on instances (`service/__init__.py:352-366`)**:
   Stock `ServiceRunner.stop()` sets `self._stop_event` and `svc["running"] = False`, but never checks for or calls `instance.stop()`. Any custom service instance managing its own loop via an instance flag never receives a shutdown signal.

## Reproduction & Validation

The test harness consists of:
- `prove.py`: Evaluates key framework properties using the Chapter 27 `HeartbeatService` and controls (plain function handler taking `ctx`, `Service` subclass via `register_service()`, and type validation checks on invalid inputs). On failure, it exits with non-zero exit code `1`; when all properties hold, it exits `0`.
- `prove.sh`: Probes the stock framework by default (`./prove.sh`, exits `1`), or applies candidate patches, tests, and verifies restoration when run with `--fixed` (`./prove.sh --fixed`, exits `0`).

### Stage 1: Stock Execution Output (Exit Code: 1)

```
==============================================================
 ServiceRunner Plain Object run() Proof — STOCK FRAMEWORK (as installed)
 tina4-python 3.13.107
==============================================================

==============================================================
 Tina4 ServiceRunner Plain Object Lifecycle Verification
==============================================================
Registered services:
  - 'heartbeat':        plain class instance with run()/stop() via register()
  - 'plain_function':   plain callable taking (ctx) via register()
  - 'subclass_service': Service subclass via register_service()

Starting ServiceRunner...
{"timestamp":"2026-08-20T13:05:29.830Z","level":"ERROR","message":"Service error","context":{"error":"'HeartbeatService' object is not callable","max_retries":3,"name":"heartbeat","retry":1}}
{"timestamp":"2026-08-20T13:05:29.831Z","level":"INFO","message":"Service started","context":{"name":"heartbeat"}}
{"timestamp":"2026-08-20T13:05:29.831Z","level":"INFO","message":"Service started","context":{"name":"plain_function"}}
{"timestamp":"2026-08-20T13:05:29.832Z","level":"INFO","message":"Service started","context":{"name":"subclass_service"}}
Running state (after ~300ms):
  heartbeat invocations:        0 (running flag: False)
  plain_function invocations:   1
  subclass_service invocations: 15

Calling ServiceRunner.stop()...
{"timestamp":"2026-08-20T13:05:30.132Z","level":"INFO","message":"Stopping all services"}
{"timestamp":"2026-08-20T13:05:30.133Z","level":"INFO","message":"Service thread exited","context":{"name":"heartbeat"}}
{"timestamp":"2026-08-20T13:05:30.133Z","level":"INFO","message":"Service thread exited","context":{"name":"plain_function"}}
{"timestamp":"2026-08-20T13:05:35.134Z","level":"INFO","message":"All services stopped"}
Stop timing:
  stop() duration: 5.0021 seconds

Post-shutdown observations:
  heartbeat running flag:        False
  subclass_service should_stop(): False

Testing invalid handler registrations:
  register('bad_int', 42) -> ACCEPTED (silent acceptance)
  register('bad_obj', <object object at 0x7faa93bb4ca0>) -> ACCEPTED (silent acceptance)

Property Evaluation:
  FAIL  Plain class instance with run() was not executed (invocations: 0)
  FAIL  Plain class instance stop() was not called on runner.stop()
  PASS  Control services executed normally (plain function and Service subclass)
  FAIL  Service subclass failed to stop promptly (duration: 5.0021s, should_stop: False)
  FAIL  Invalid handlers accepted silently at registration time (0/2 rejected)
==============================================================
 VERDICT: 4 property/properties broken (ServiceRunner plain object bug confirmed)
==============================================================
```

## Candidate Fix Proof

The fix is provided in two sequential candidate patches applied to `service/__init__.py`:

1. `../.fw16-candidate.patch`: Updates `ServiceRunner.stop()` to check for `svc.get("instance")` and call `instance.stop()`.
2. `../.fw02-candidate.patch`: Updates `ServiceRunner.register()` to detect non-callable objects possessing a callable `run()` method. When found, it adapts them into `actual_handler = lambda _ctx=None: instance.run()`, sets `daemon = True` (as the object owns its loop), and stores `instance` so `stop()` can signal it. If the handler is neither callable nor an object with `run()`, it raises `TypeError(f"handler for '{name}' must be callable")`.

**Why `.fw16-candidate.patch` must be applied first:**
- The patch `.fw02-candidate.patch` is created against the code after `.fw16-candidate.patch` modifications.
- Functionally, `fw02` adapts plain objects with `run()` by setting `daemon = True` and retaining `instance` in `service_entry["instance"]`. Without `fw16`'s addition to `ServiceRunner.stop()`, the runner would have no mechanism to invoke `instance.stop()`, leaving plain services looping indefinitely until thread timeout.

### Stage 3: Patched Execution Output (Exit Code: 0)

```
Applying candidate patches to service/__init__.py...
  Stock MD5: 332d3e38acdbc418d3b19994c6e43e5c
  Applying patch 1: .fw16-candidate.patch...
  Applying patch 2: .fw02-candidate.patch...
  Patched MD5: fa945cf3a45806b7ccb5d934ba9dee08

==============================================================
 ServiceRunner Plain Object run() Proof — WITH CANDIDATE FIXES (.fw16 + .fw02)
 tina4-python 3.13.107
==============================================================

==============================================================
 Tina4 ServiceRunner Plain Object Lifecycle Verification
==============================================================
Registered services:
  - 'heartbeat':        plain class instance with run()/stop() via register()
  - 'plain_function':   plain callable taking (ctx) via register()
  - 'subclass_service': Service subclass via register_service()

Starting ServiceRunner...
{"timestamp":"2026-08-20T13:05:39.029Z","level":"INFO","message":"Service started","context":{"name":"heartbeat"}}
{"timestamp":"2026-08-20T13:05:39.030Z","level":"INFO","message":"Service started","context":{"name":"plain_function"}}
{"timestamp":"2026-08-20T13:05:39.030Z","level":"INFO","message":"Service started","context":{"name":"subclass_service"}}
Running state (after ~300ms):
  heartbeat invocations:        6 (running flag: True)
  plain_function invocations:   1
  subclass_service invocations: 15

Calling ServiceRunner.stop()...
{"timestamp":"2026-08-20T13:05:39.330Z","level":"INFO","message":"Stopping all services"}
{"timestamp":"2026-08-20T13:05:39.331Z","level":"INFO","message":"Service thread exited","context":{"name":"plain_function"}}
{"timestamp":"2026-08-20T13:05:39.332Z","level":"INFO","message":"Service thread exited","context":{"name":"heartbeat"}}
{"timestamp":"2026-08-20T13:05:39.333Z","level":"INFO","message":"Service thread exited","context":{"name":"subclass_service"}}
{"timestamp":"2026-08-20T13:05:39.333Z","level":"INFO","message":"All services stopped"}
Stop timing:
  stop() duration: 0.0031 seconds

Post-shutdown observations:
  heartbeat running flag:        False
  subclass_service should_stop(): True

Testing invalid handler registrations:
  register('bad_int', 42) -> REJECTED with TypeError ('bad_int' in message)
  register('bad_obj', <object object at 0x7feb8e2e4cf0>) -> REJECTED with TypeError ('bad_obj' in message)

Property Evaluation:
  PASS  Plain class instance with run() executed (6 invocations)
  PASS  Plain class instance stop() called on runner.stop() (running flag cleared)
  PASS  Control services executed normally (plain function and Service subclass)
  PASS  Service subclass stopped promptly (0.0031s < 1.0s)
  PASS  Invalid handlers rejected at registration time with TypeError
==============================================================
 VERDICT: All properties hold (ServiceRunner plain object support verified)
==============================================================

Restoring stock framework...
  restore verified (md5 332d3e38acdbc418d3b19994c6e43e5c)
```

## Restoration Verification

All automated tests in `prove.sh --fixed` use an EXIT trap to ensure that the installed virtual environment is restored to true stock condition. The file `.venv/lib/python3.13/site-packages/tina4_python/service/__init__.py` has been verified with MD5 checksum `332d3e38acdbc418d3b19994c6e43e5c`, confirming that the repository and virtual environment are left completely unpatched.
