# Tina4 ServiceRunner Class-Based Service Shutdown Thread Leak

## Overview

In `tina4-python` 3.13.107, `ServiceRunner.stop()` fails to stop class-based services registered via `register_service()`, leaking their background worker threads. When `ServiceRunner.stop()` is executed, it sets its internal `_stop_event`, marks dictionary state `svc["running"] = False`, and joins each thread with a 5-second timeout, but never calls `stop()` on the registered `Service` instance. Because `Service.should_stop()` checks `self._running` (which is only cleared by `Service.stop()`), class-based service loops (`while not self.should_stop():`) never exit, causing `ServiceRunner.stop()` to block for the full 5-second join timeout and leave orphaned threads running in the background.

This behavior breaks the documented framework lifecycle contract in `docs/python/27-service-runner.md:224`, which explicitly promises:
> "`stop()` calls `stop()` on each registered service and waits for their threads to finish."

---

## Environment and Versions

- **tina4-python**: `3.13.107`
- **tina4 CLI**: `3.8.77`
- **Date**: 2026-08-20
- **Stock MD5 (`service/__init__.py`)**: `332d3e38acdbc418d3b19994c6e43e5c`
- **Environment Status**: The virtual environment (`.venv`) is left unpatched. Restoration after `--fixed` execution is verified against the stock MD5 checksum.

---

## Root Cause Analysis

The root cause exists in `tina4_python/service/__init__.py`.

### 1. `instance` Key Stored but Never Read (`tina4_python/service/__init__.py:313-325`)

```python
313|        self.services.append({
314|            "name": name,
315|            "handler": service,  # Service instances are callable (see __call__)
316|            "interval": 0,
317|            "cron": None,
318|            "daemon": True,  # Service subclasses manage their own loop
319|            "max_retries": max_retries,
320|            "retries": 0,
321|            "running": False,
322|            "last_run": None,
323|            "started_at": None,
324|            "instance": service,  # keep reference so stop() can route to service.stop()
325|        })
```

Line 324 records `"instance": service` with an explicit code comment stating the reference is kept so `stop()` can route to `service.stop()`. However, grepping the codebase reveals that the `"instance"` key is never read anywhere.

### 2. `ServiceRunner.stop()` Fails to Call `instance.stop()` (`tina4_python/service/__init__.py:352-367`)

```python
352|    def stop(self):
353|        """Stop all running services gracefully."""
354|        _get_log().info("Stopping all services")
355|        self._stop_event.set()
356|
357|        for svc in self.services:
358|            svc["running"] = False
359|
360|        # Give threads a moment to finish
361|        for t in self._threads:
362|            t.join(timeout=5)
363|
364|        self._threads.clear()
365|        self._started = False
366|        _get_log().info("All services stopped")
```

`ServiceRunner.stop()` sets `self._stop_event` and modifies `svc["running"] = False` on the service dictionary entry, but never invokes `instance.stop()`.

### 3. `Service.should_stop()` Checks `self._running` (`tina4_python/service/__init__.py:211-236`)

```python
211|    def __init__(self):
212|        self._running = True
...
220|    def stop(self) -> None:
221|        """Signal this service to stop. Override for custom shutdown behaviour
222|        but always call ``super().stop()`` so the internal flag gets set —
223|        ``should_stop()`` reads from it.
224|        """
225|        self._running = False
226|
227|    def should_stop(self) -> bool:
...
235|        return not self._running
```

Because `instance.stop()` is never called, `self._running` remains `True`. The worker loop `while not self.should_stop():` continues spinning indefinitely. `t.join(timeout=5)` times out after 5 seconds, after which `ServiceRunner.stop()` discards its thread handle in `self._threads.clear()`, leaving an unmanaged, leaked thread active in the Python process.

### Control Contrast

Plain callables registered via `register()` receive a `ServiceContext` instance whose `stop_event` references `ServiceRunner._stop_event`. Because line 355 calls `self._stop_event.set()`, plain callables watching `ctx.stop_event` terminate immediately.

---

## Reproduction

Run `prove.py` or `prove.sh` directly from this directory:

```bash
# Probes stock framework
./prove.sh

# Probes with candidate fix and restores venv
./prove.sh --fixed
```

---

## Evidence

### Stock Framework (`evidence/stage1-stock.txt`)

```text
==============================================================
 ServiceRunner Stop Thread Leak Proof — STOCK FRAMEWORK (as installed)
 tina4-python 3.13.107
==============================================================

==============================================================
 Tina4 ServiceRunner Shutdown Lifecycle Verification
==============================================================
Registered services:
  - 'control_service': plain callable via register(daemon=True), watching ctx.stop_event
  - 'class_service':   Service subclass via register_service(), watching self.should_stop()

Starting ServiceRunner...
{"timestamp":"2026-08-20T12:59:50.727Z","level":"INFO","message":"Service started","context":{"name":"control_service"}}
{"timestamp":"2026-08-20T12:59:50.727Z","level":"INFO","message":"Service started","context":{"name":"class_service"}}
Running state (after ~200ms):
  control_service counter: 20
  class_service counter:   20

Calling ServiceRunner.stop()...
{"timestamp":"2026-08-20T12:59:50.928Z","level":"INFO","message":"Stopping all services"}
{"timestamp":"2026-08-20T12:59:50.930Z","level":"INFO","message":"Service thread exited","context":{"name":"control_service"}}
{"timestamp":"2026-08-20T12:59:55.931Z","level":"INFO","message":"All services stopped"}
Stop timing:
  stop() duration: 5.0036 seconds

Post-shutdown observations:
  Control Callable ('control_service'):
    - Thread 'svc-control_service' alive at stop return: False
    - Counter at stop return:   20
    - Counter 200ms later:      20 (delta: 0)
    - Thread alive 200ms later: False

  Class-based Service ('class_service'):
    - Thread 'svc-class_service' alive at stop return:   True
    - Counter at stop return:   510
    - Counter 200ms later:      529 (delta: 19)
    - Thread alive 200ms later: True

Property Evaluation:
  PASS  Control service terminated promptly (stop_event observed)
  FAIL  stop() blocked for thread join timeout (5.0036s >= 1.0s, expected prompt exit)
  FAIL  Class service thread 'svc-class_service' leaked in threading.enumerate()
  FAIL  Class service continued running after stop (counter advanced by 19)
==============================================================
 VERDICT: 3 property/properties broken (Service stop leaked thread)
==============================================================
```

### With Candidate Fix (`evidence/stage3-fixed.txt`)

```text
Applying candidate patch to service/__init__.py...
  patch applied successfully

==============================================================
 ServiceRunner Stop Thread Leak Proof — WITH CANDIDATE FIX (.fw16-candidate.patch)
 tina4-python 3.13.107
==============================================================

==============================================================
 Tina4 ServiceRunner Shutdown Lifecycle Verification
==============================================================
Registered services:
  - 'control_service': plain callable via register(daemon=True), watching ctx.stop_event
  - 'class_service':   Service subclass via register_service(), watching self.should_stop()

Starting ServiceRunner...
{"timestamp":"2026-08-20T12:59:56.865Z","level":"INFO","message":"Service started","context":{"name":"control_service"}}
{"timestamp":"2026-08-20T12:59:56.865Z","level":"INFO","message":"Service started","context":{"name":"class_service"}}
Running state (after ~200ms):
  control_service counter: 20
  class_service counter:   20

Calling ServiceRunner.stop()...
{"timestamp":"2026-08-20T12:59:57.065Z","level":"INFO","message":"Stopping all services"}
{"timestamp":"2026-08-20T12:59:57.069Z","level":"INFO","message":"Service thread exited","context":{"name":"class_service"}}
{"timestamp":"2026-08-20T12:59:57.070Z","level":"INFO","message":"Service thread exited","context":{"name":"control_service"}}
{"timestamp":"2026-08-20T12:59:57.070Z","level":"INFO","message":"All services stopped"}
Stop timing:
  stop() duration: 0.0050 seconds

Post-shutdown observations:
  Control Callable ('control_service'):
    - Thread 'svc-control_service' alive at stop return: False
    - Counter at stop return:   20
    - Counter 200ms later:      20 (delta: 0)
    - Thread alive 200ms later: False

  Class-based Service ('class_service'):
    - Thread 'svc-class_service' alive at stop return:   False
    - Counter at stop return:   20
    - Counter 200ms later:      20 (delta: 0)
    - Thread alive 200ms later: False

Property Evaluation:
  PASS  Control service terminated promptly (stop_event observed)
  PASS  stop() completed promptly (0.0050s < 1.0s)
  PASS  Class service thread 'svc-class_service' terminated cleanly
  PASS  Class service stopped executing (counter did not advance after stop)
==============================================================
 VERDICT: All properties hold (Service shutdown cleanly)
==============================================================
  venv restored from backup
  restore verified (md5 332d3e38acdbc418d3b19994c6e43e5c)
```

---

## Candidate Patch Summary

The candidate patch (`../.fw16-candidate.patch`) iterates over `self.services` inside `ServiceRunner.stop()`, inspects `svc.get("instance")`, and calls `instance.stop()` if callable:

```python
         for svc in self.services:
             svc["running"] = False
+            instance = svc.get("instance")
+            if instance is not None and hasattr(instance, "stop") and callable(instance.stop):
+                try:
+                    instance.stop()
+                except Exception as exc:
+                    _get_log().error(
+                        "Error stopping service instance",
+                        name=svc.get("name"),
+                        error=str(exc),
+                    )
```

This properly triggers `Service.stop()`, updating `self._running = False`, allowing `Service.should_stop()` to return `True`, and gracefully exiting the service worker thread in milliseconds without leaks.
