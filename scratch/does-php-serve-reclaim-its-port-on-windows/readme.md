# Does php `serve` reclaim its port from a stale Tina4 server on Windows?

**No.** Start a second `tina4php serve` on a port that a stale Tina4 dev server still holds.
It prints `Warning: Reclaimed port 17992 from Tina4 dev server (PID: 5432).` and starts, but
PID 5432 is never stopped. Eight seconds later both servers are running, and the stale one is
still the one answering requests.

**This only happens on Windows.** It was found on 2026-09-30, while verifying the `f-auth-01`
fix on a Windows 11 VM. That fix's port-reclaim test is posix-only because of this bug.
Ledger row: `f-cli-32`.

The run used:
- tina4-php `origin/v3` `44b63aee` (the banner says v3.13.141), with stock `Tina4/` and
  `bin/tina4php`;
- PHP 8.4.25 NTS, which has no posix extension;
- Windows 11 build 26200.

## Mechanism

`bin/tina4php:2160` runs the takeover on every `serve`, before the server starts.

`Tina4/PortTakeover.php:203-210`:

```php
private static function killPid(int $pid): bool
{
    if (function_exists('posix_kill')) {
        return @posix_kill($pid, defined('SIGTERM') ? SIGTERM : 15);
    }
    @exec("kill -15 {$pid}");
    return true;
}
```

PHP on Windows has no posix extension, so every takeover goes through the `exec` fallback.
`cmd.exe` has no `kill`: the server's console shows `'kill' is not recognized as an internal
or external command`. The function returns `true` without checking the result.

`takeOverPort()` (`:265-281`) then does four things:
- counts the PID as killed;
- deletes the stale server's pidfile;
- sleeps for the grace period;
- returns `KILLED`.

`bin/tina4php:1492` prints the `KILLED` message as the warning above. Everything before the
kill works on Windows. `portHolders()` (`:178`) finds the holder through `netstat -ano`, and
the pidfile identifies it as Tina4.

The new server's bind still succeeds, and that hides the failure. PHP's `stream_socket_server`
sets `SO_REUSEADDR`. On Windows, that lets a second listener bind a port another socket is
already listening on. Nothing fails and nothing says so. Requests keep going to the old
process, which still has the old code loaded.

These follow from the mechanism but were not run:

- The stale server still holds the port but its pidfile is gone. A third `serve` on that port
  should therefore find a holder with no pidfile, and refuse it as a non-Tina4 process.
- Any Windows PHP without posix takes the same path, not only this build.

## Reproduce

Run `win/takeover.ps1` on the Windows guest:

    powershell -NoProfile -ExecutionPolicy Bypass -File takeover.ps1 -Root <dir> -Php <php.exe> -Port <free port>

`<dir>\tree` must be a tina4-php checkout with `composer install` done. The script:
1. builds a two-file app with a `/pid` route;
2. starts one `serve --managed` on the port, then starts a second;
3. waits 8 seconds;
4. prints which servers are running, which one answers, the second server's console output,
   and the port's listeners;
5. kills both with `taskkill /T /F`, and prints anything left listening.

The output is in `evidence/win-takeover-stock.txt`. The key lines are:

    stale server: process 5432, answering as pid 5432
    pid files naming the port: …\takeover-app\data\.tina4-serve-17992.pid
    after 8 s: stale running=True  second running=True  answering pid=5432
      Warning: Reclaimed port 17992 from Tina4 dev server (PID: 5432).
    'kill' is not recognized as an internal or external command,

## Bounds

- **What was run:** PHP 8.4.25 NTS only, on one Windows build. `serve --managed` was started
  directly. The Rust `tina4` CLI was not used; it has its own takeover, which was not checked.
- **Not established:** which process PID 4136 was. The listener table shows `127.0.0.1:17992`
  and `::1:17992`, both under PID 4136, and no entry for 5432, yet 5432 kept answering. The
  script does not print the second server's PID. A rerun should print `$second.Id` and
  `netstat -ano`.
- **Other ports (source read, nothing run on Windows):**
  - python (`tina4_python/core/port_takeover.py:299`) calls `os.kill(pid, SIGTERM)`. Python's
    docs say that on Windows this calls `TerminateProcess`.
  - nodejs (`packages/core/src/portTakeover.ts:228`) calls `process.kill(pid, "SIGTERM")`.
    Node's docs say that on Windows this kills the process.
  - ruby (`lib/tina4/port_takeover.rb:195`) calls `Process.kill("TERM", pid)`. Ruby's Windows
    `kill()` (ruby/ruby `win32/win32.c:5008-5108`) handles only signals 0, INT and KILL, and
    sets `EINVAL` for anything else. The resulting `Errno::EINVAL` is not caught by the
    port's `rescue Errno::ESRCH, Errno::EPERM`, so its takeover should raise.
- **Found on the way (read, not run):** on Windows, `portHolders()` matches `":{$port}"` as a
  substring of each `netstat` line, in either address column. Port 800 therefore also matches
  a listener on 8000, and a client connected to the port counts as a holder too. The pidfile
  check keeps it from killing the wrong process. The expected effect is a false
  `held by a non-Tina4 process` notice.
