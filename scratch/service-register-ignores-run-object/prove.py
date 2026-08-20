#!/usr/bin/env python3
"""
prove.py - Reproduction and validation script for Tina4 Python ServiceRunner issue.

Tests whether ServiceRunner.register() accepts plain class instances with a run()
method (as documented in Chapter 27 of official docs) and verifies the candidate fix.
"""

import sys
import time
from tina4_python.service import ServiceRunner, Service


class HeartbeatService:
    """Verbatim shape from Chapter 27 (lines 19-32) of the official documentation."""

    def __init__(self, interval=0.05):
        self.interval = interval
        self.running = False
        self.invocations = 0

    def run(self):
        self.running = True
        while self.running:
            self.invocations += 1
            time.sleep(self.interval)

    def stop(self):
        self.running = False


class SubclassService(Service):
    """Control: standard Service subclass registered via register_service()."""

    def __init__(self):
        super().__init__()
        self.invocations = 0

    def run(self):
        while not self.should_stop():
            self.invocations += 1
            time.sleep(0.02)


def main() -> int:
    print("==============================================================")
    print(" Tina4 ServiceRunner Plain Object Lifecycle Verification")
    print("==============================================================")

    runner = ServiceRunner()

    # 1. Target: Chapter 27 HeartbeatService
    heartbeat = HeartbeatService(interval=0.05)
    try:
        runner.register("heartbeat", heartbeat)
        print("Registered services:")
        print("  - 'heartbeat':        plain class instance with run()/stop() via register()")
    except Exception as exc:
        print(f"[REGISTER] heartbeat FAILED to register: {exc}")
        return 1

    # 2. Control 1: Function-style handler taking ctx
    fn_invocations = 0

    def plain_fn(ctx):
        nonlocal fn_invocations
        fn_invocations += 1

    runner.register("plain_function", plain_fn, interval=1)
    print("  - 'plain_function':   plain callable taking (ctx) via register()")

    # 3. Control 2: Service subclass via register_service()
    subclass_svc = SubclassService()
    runner.register_service("subclass_service", subclass_svc)
    print("  - 'subclass_service': Service subclass via register_service()")
    print()

    # Start services
    print("Starting ServiceRunner...")
    runner.start()

    # Allow services time to execute multiple cycles
    time.sleep(0.3)

    hb_ticks_running = heartbeat.invocations
    hb_state_running = heartbeat.running
    fn_ticks_running = fn_invocations
    sub_ticks_running = subclass_svc.invocations

    print("Running state (after ~300ms):")
    print(f"  heartbeat invocations:        {hb_ticks_running} (running flag: {hb_state_running})")
    print(f"  plain_function invocations:   {fn_ticks_running}")
    print(f"  subclass_service invocations: {sub_ticks_running}")
    print()

    # Stop services
    print("Calling ServiceRunner.stop()...")
    stop_start = time.perf_counter()
    runner.stop()
    stop_duration = time.perf_counter() - stop_start
    print("Stop timing:")
    print(f"  stop() duration: {stop_duration:.4f} seconds")
    print()

    hb_state_stopped = heartbeat.running
    sub_should_stop = subclass_svc.should_stop()

    print("Post-shutdown observations:")
    print(f"  heartbeat running flag:        {hb_state_stopped}")
    print(f"  subclass_service should_stop(): {sub_should_stop}")
    print()

    # Test bad handler registrations
    print("Testing invalid handler registrations:")
    invalid_inputs = [("bad_int", 42), ("bad_obj", object())]
    rejected_count = 0
    for name, bad_val in invalid_inputs:
        try:
            test_runner = ServiceRunner()
            test_runner.register(name, bad_val)
            print(f"  register('{name}', {bad_val!r}) -> ACCEPTED (silent acceptance)")
        except TypeError as exc:
            if name in str(exc):
                print(f"  register('{name}', {bad_val!r}) -> REJECTED with TypeError ('{name}' in message)")
                rejected_count += 1
            else:
                print(f"  register('{name}', {bad_val!r}) -> REJECTED with TypeError but missing name: {exc}")
        except Exception as exc:
            print(f"  register('{name}', {bad_val!r}) -> REJECTED with unexpected exception: {exc}")
    print()

    # Property Checks
    failures = 0
    print("Property Evaluation:")

    # 1. Registered plain class instance with run() must execute in background thread
    if hb_ticks_running > 0 and hb_state_running is True:
        print(f"  PASS  Plain class instance with run() executed ({hb_ticks_running} invocations)")
    else:
        print(f"  FAIL  Plain class instance with run() was not executed (invocations: {hb_ticks_running})")
        failures += 1

    # 2. Registered plain class instance with stop() must have stop() invoked by runner.stop()
    if hb_ticks_running > 0 and hb_state_stopped is False:
        print("  PASS  Plain class instance stop() called on runner.stop() (running flag cleared)")
    else:
        print("  FAIL  Plain class instance stop() was not called on runner.stop()")
        failures += 1

    # 3. Control services (callable taking ctx, Service subclass) must execute normally
    if fn_ticks_running >= 1 and sub_ticks_running >= 1:
        print("  PASS  Control services executed normally (plain function and Service subclass)")
    else:
        print("  FAIL  Control services failed to execute properly")
        failures += 1

    # 4. Service subclass must stop promptly via should_stop() on runner.stop()
    if sub_should_stop is True and stop_duration < 1.0:
        print(f"  PASS  Service subclass stopped promptly ({stop_duration:.4f}s < 1.0s)")
    else:
        print(f"  FAIL  Service subclass failed to stop promptly (duration: {stop_duration:.4f}s, should_stop: {sub_should_stop})")
        failures += 1

    # 5. Invalid handlers without run() must be rejected with TypeError at registration time
    if rejected_count == len(invalid_inputs):
        print("  PASS  Invalid handlers rejected at registration time with TypeError")
    else:
        print(f"  FAIL  Invalid handlers accepted silently at registration time ({rejected_count}/{len(invalid_inputs)} rejected)")
        failures += 1

    print("==============================================================")
    if failures == 0:
        print(" VERDICT: All properties hold (ServiceRunner plain object support verified)")
    else:
        print(f" VERDICT: {failures} property/properties broken (ServiceRunner plain object bug confirmed)")
    print("==============================================================")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

