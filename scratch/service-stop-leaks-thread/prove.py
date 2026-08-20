#!/usr/bin/env python3
"""Proof: ServiceRunner.stop() fails to stop class-based Service instances, leaking threads.

Tests both:
1. Control: A plain callable registered with register() observing ctx.stop_event.
2. Target: A class subclassing Service registered with register_service(),
   whose run() loop uses `while not self.should_stop():`.
"""

import sys
import time
import threading
from tina4_python.service import Service, ServiceRunner


class CountingService(Service):
    """Class-based service following the documented Service pattern."""

    def __init__(self):
        super().__init__()
        self.counter = 0

    def run(self):
        while not self.should_stop():
            self.counter += 1
            time.sleep(0.01)


control_counter = 0


def control_callable(ctx):
    """Control service: plain callable registered via register()."""
    global control_counter
    while not ctx.stop_event.is_set():
        control_counter += 1
        time.sleep(0.01)


def main():
    global control_counter
    control_counter = 0

    runner = ServiceRunner()
    class_service = CountingService()

    runner.register("control_service", control_callable, daemon=True)
    runner.register_service("class_service", class_service)

    print("==============================================================")
    print(" Tina4 ServiceRunner Shutdown Lifecycle Verification")
    print("==============================================================")
    print("Registered services:")
    print("  - 'control_service': plain callable via register(daemon=True), watching ctx.stop_event")
    print("  - 'class_service':   Service subclass via register_service(), watching self.should_stop()")
    print()

    print("Starting ServiceRunner...")
    runner.start()

    # Let services run for 200 ms to accumulate counts
    time.sleep(0.2)

    ctrl_before = control_counter
    class_before = class_service.counter
    print(f"Running state (after ~200ms):")
    print(f"  control_service counter: {ctrl_before}")
    print(f"  class_service counter:   {class_before}")
    print()

    print("Calling ServiceRunner.stop()...")
    t0 = time.perf_counter()
    runner.stop()
    stop_duration = time.perf_counter() - t0

    ctrl_at_stop = control_counter
    class_at_stop = class_service.counter

    active_threads_at_stop = {t.name for t in threading.enumerate() if t.is_alive()}
    ctrl_thread_alive = "svc-control_service" in active_threads_at_stop
    class_thread_alive = "svc-class_service" in active_threads_at_stop

    # Wait another 200 ms to check if background threads are still running and incrementing
    time.sleep(0.2)
    ctrl_after = control_counter
    class_after = class_service.counter

    active_threads_after = {t.name for t in threading.enumerate() if t.is_alive()}
    ctrl_thread_alive_after = "svc-control_service" in active_threads_after
    class_thread_alive_after = "svc-class_service" in active_threads_after

    print(f"Stop timing:")
    print(f"  stop() duration: {stop_duration:.4f} seconds")
    print()

    print("Post-shutdown observations:")
    print(f"  Control Callable ('control_service'):")
    print(f"    - Thread 'svc-control_service' alive at stop return: {ctrl_thread_alive}")
    print(f"    - Counter at stop return:   {ctrl_at_stop}")
    print(f"    - Counter 200ms later:      {ctrl_after} (delta: {ctrl_after - ctrl_at_stop})")
    print(f"    - Thread alive 200ms later: {ctrl_thread_alive_after}")
    print()
    print(f"  Class-based Service ('class_service'):")
    print(f"    - Thread 'svc-class_service' alive at stop return:   {class_thread_alive}")
    print(f"    - Counter at stop return:   {class_at_stop}")
    print(f"    - Counter 200ms later:      {class_after} (delta: {class_after - class_at_stop})")
    print(f"    - Thread alive 200ms later: {class_thread_alive_after}")
    print()

    # Property Checks
    failures = 0

    print("Property Evaluation:")

    # 1. Control callable stops promptly and cleanly
    if not ctrl_thread_alive and (ctrl_after == ctrl_at_stop):
        print("  PASS  Control service terminated promptly (stop_event observed)")
    else:
        print("  FAIL  Control service failed to stop promptly")
        failures += 1

    # 2. Class-based service should stop promptly (< 1.0s, join timeout is 5.0s)
    if stop_duration < 1.0:
        print(f"  PASS  stop() completed promptly ({stop_duration:.4f}s < 1.0s)")
    else:
        print(f"  FAIL  stop() blocked for thread join timeout ({stop_duration:.4f}s >= 1.0s, expected prompt exit)")
        failures += 1

    # 3. Class-based service thread should not be leaked
    if not class_thread_alive and not class_thread_alive_after:
        print("  PASS  Class service thread 'svc-class_service' terminated cleanly")
    else:
        print("  FAIL  Class service thread 'svc-class_service' leaked in threading.enumerate()")
        failures += 1

    # 4. Class-based service should stop incrementing
    if class_after == class_at_stop:
        print("  PASS  Class service stopped executing (counter did not advance after stop)")
    else:
        print(f"  FAIL  Class service continued running after stop (counter advanced by {class_after - class_at_stop})")
        failures += 1

    print("==============================================================")
    if failures == 0:
        print(" VERDICT: All properties hold (Service shutdown cleanly)")
    else:
        print(f" VERDICT: {failures} property/properties broken (Service stop leaked thread)")
    print("==============================================================")

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
