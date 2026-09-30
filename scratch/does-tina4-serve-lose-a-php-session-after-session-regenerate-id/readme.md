# Does `tina4 serve` lose a php session after `session_regenerate_id()`?

Asked by tina4-php issue #253 and its follow-up comment. Ledger rows `f-auth-01`, `f-auth-02`,
`f-cli-31` and `f-cli-32`. Run on Linux (Fedora 43) and Windows 11 (build 26200) with PHP 8.4.25 and
CLI 3.8.94, on 2026-09-30.

**Yes, and which of two defects an app hits depends on its entry file.**

- **The entry file leaves an output buffer open**, meaning an `ob_start()` that is never closed.
  - Under `tina4 serve` on 3.13.139 and 3.13.141, the native session works until a handler
    regenerates the id.
  - The new id is then never sent, and the next request has lost the session. That is issue
    #253 (`f-auth-02`).
  - Reproduced on Linux and Windows.
  - **Fixed upstream** by `f6fbd8a4` (tina4-php#254, merged 2026-09-30 as `c48acab5`), which
    closed #253. That commit is in no release yet; the newest tag is 3.13.141.
- **The entry file leaves no buffer open**, like the `tina4 init php` scaffold.
  - Here the native session never starts under `tina4 serve` at all: not on any version tested
    (3.11.20 to v3 `c48acab5`), and not on either OS.
  - No `PHPSESSID` cookie is ever sent, and the issue's own `/regen` route answers **500**
    (`f-auth-01`).
  - The #253 fix does not touch this. Its test cannot see it, because the test suppresses the
    startup banner that causes it.

**"It worked on 3.13.138" is true in one sense only.**

- Some servers run every request in one PHP process: Windows always does, and Linux does up to
  3.13.94 or with `TINA4_SERVE_FORK=false`.
- There, 3.13.138 never closed or reset the session between requests, so **every client shared
  one session**. With an open buffer, that shared session even survived a regenerate.
- 3.13.139's per-request reset (ADR-0079 s5) closed that cross-client leak, and exposed both
  defects.

## Mechanism

**Startup output decides whether the session can start.**

- The `serve` command echoes its banner before the socket server runs (`bin/tina4php:2218-2229`
  on 3.13.141 and v3, `:2205-2216` on 3.13.138).
- With debug off, the first output is instead a port-takeover refusal at `:1496`. It claims a
  free port "is in use" (`f-cli-31`).
- The PHP command-line build hardcodes `output_buffering=0`, which overrides `php.ini`
  (`php-src sapi/cli/php_cli.c:120` on PHP-8.4, `:133` on 8.2 and 8.3, read). This box's
  `/etc/php.ini` sets 4096, yet the CLI reports 0 (run).
- So the first `echo` marks headers as sent for the life of the process, **unless an output
  buffer is open to catch it**.
- A write through a stream does not mark headers as sent. `Log` writes with
  `fwrite(STDOUT, ...)` (`Tina4/Log.php:513-515` on v3), and its lines printed while the session
  still worked (run).
- `serve` includes the app's `index.php` inside its own `ob_start()` / `ob_end_clean()` pair
  (`bin/tina4php:2198-2201`).
- If the app opens a buffer of its own and leaves it, that `ob_end_clean()` closes the app's
  buffer instead. `serve`'s buffer is left open, and the banner lands in it.

**`f-auth-01`, no open buffer.**

- `Router::startNativeSession()` only calls `session_start()` when `!headers_sent()`.
  - That is `Tina4/Router.php:1246` on 3.13.141 and `:1221` on 3.13.138.
  - The guard has been there since `10dfbb53`, first released in 3.11.20.
- It never does. `/probe` reports `status: 1`, `id: ""`, `headers_sent: "tina4php:2228"`.

**`f-auth-02`, open buffer.** This is the issue's mechanism, confirmed.

- `routerNativeSessionIsNew` is set once, at session start (`Router.php:1285`).
- `finishNativeSession()` emits the cookie only when that flag is set (`:1315`). An id changed
  later by `session_regenerate_id()` never reaches the client.
- It came in with `a7b9f008` (ADR-0079), first released in 3.13.139.
- `f6fbd8a4` replaces the flag with a comparison against the id the client sent. The cookie is
  now emitted whenever `session_id()` differs from that id.

**What 3.13.139 changed.** 3.13.138 never reset `$_SESSION` or closed the session between
requests.

- In one process where no session started, `$_SESSION` is a plain process-global array.
- In one process where a session did start, it stays active for every later request.
- Either way, every client shares it.

Windows is always one process. Without `pcntl_fork`, `Server::resolveForkPerRequest()` returns
false (`Server.php:1456-1468`, read). Linux forked per request from 3.13.95 (`b93f5f94`).

3.13.139 added `$_SESSION = []` per request (`Router.php:1235-1244`), which is correct. The
reset skips a session the app started itself, which is why a pre-started session stays shared.

## Proof

`./prove.sh` (Linux) and `win/prove.ps1` (Windows, `powershell -File`) do three things:

1. Install each version from Packagist. `v3.x-dev` is Packagist's name for the v3 branch head.
2. Serve `app/` under each mode:
   - `cli`: `tina4 serve`.
   - `direct`: the bare socket server.
   - `serial`: the bare socket server with `TINA4_SERVE_FORK=false`. Windows is always serial.
   - `buffered`: an instrument, `php -d output_buffering=4096`.
   - `phps`: `php -S`.
3. Drive the issue's three requests with a cookie jar, plus these controls:
   - `/set` writes the session without regenerating.
   - `/regen-keep` calls `regenerate(false)`.
   - `/t-set` and `/t-regen` do the same through Tina4's own `$request->session`.

A fresh client that sees an earlier client's `hit` is flagged `SHARED`. App variants:

- `OB_APP=1`: `index.php` opens a buffer and leaves it open.
- `PRESTART=1`: `index.php` calls `session_start()` itself.

`./upstream-fixture.sh` runs upstream's own #253 regression fixture, taken from the installed v3
commit. It runs once with the banner suppressed, as upstream's test does, and once without.

`./scaffold.sh` runs the issue's curl sequence against a real `tina4 init php` project with
only the issue's two routes added. Pass `VERSION=v3.x-dev` to move that project onto the v3
head.

- On 3.13.141 and on v3 `c48acab5`, it gets no cookie, then a 500, then an empty session
  (`evidence/run-scaffold.txt`).
- As an instrument, one `ob_start()` was added to that `index.php` on v3 and later reverted.
  With it, the same script reported the session kept through `/regen`.

`upstream-comment-253.md` is the comment posted on the closed issue on 2026-09-30
(https://github.com/tina4stack/tina4-php/issues/253#issuecomment-5917365652).

All output is in `evidence/`: `run-*.txt` on Linux, `win-run-*.txt` on Windows.

The native session as one client sees it, under `tina4 serve`:

**No open buffer (the scaffold's entry file):**

| version | Linux, default | Linux, `TINA4_SERVE_FORK=false` | Windows |
|---|---|---|---|
| 3.11.20 | shared by every client (no fork yet) | shared | not run |
| 3.13.94 | shared (no fork yet) | shared | not run |
| 3.13.95 | lost (forks per request) | shared | not run |
| 3.13.138 | lost | shared | shared |
| 3.13.139 | lost | lost | lost |
| 3.13.141 | lost | lost | lost |
| v3 `c48acab5` | lost | lost | not run |

`/regen` answers 500 in every cell here:
`session_regenerate_id(): Session ID cannot be regenerated when there is no active session`.

**Open buffer (`OB_APP=1`):**

| version | Linux, default | Linux, `TINA4_SERVE_FORK=false` | Windows |
|---|---|---|---|
| 3.13.138 | lost: no native cookie is ever sent | shared, surviving `/regen` | shared, surviving `/regen` |
| 3.13.139 | `/set` kept, **`/regen` lost** | same | same |
| 3.13.141 | `/set` kept, **`/regen` lost** | same | same |
| v3 `c48acab5` | kept through `/regen` | kept through `/regen` | not run |

On 3.13.139 and 3.13.141, the `/regen` flow runs as follows:

1. Step 1 sets `PHPSESSID=A`.
2. Step 2 answers with a new id and sends no cookie.
3. Step 3 comes back with a third id and `hit null`.

This matches the issue except for one detail in step 3. The issue shows the old id A coming
back. With `session_regenerate_id(true)`, A's file has been deleted, so strict mode issues a
fresh id instead. A comes back, empty, only with `regenerate(false)` (`/regen-keep`).

**Pre-start (`PRESTART=1`):** 3.13.138, 3.13.139, 3.13.141 and v3 behave identically. The
first three were run on both OSes; v3 was run on Linux only.

- One boot-time session serves every client.
- Writes are lost under fork, and shared between clients in one process.
- No `PHPSESSID` is ever sent.
- `/regen` answers 500 (`... after headers have already been sent`).

Under `serve`, `index.php` runs once per process, so a `session_start()` there cannot be per
request. The follow-up's claim ("3.13.138 tolerated a pre-started session, 3.13.139 does not")
did not reproduce.

**Upstream's own fixture (`./upstream-fixture.sh`, v3 `c48acab5`):**

- With `TINA4_SUPPRESS=true`, the session is kept through `/regen`, and the new cookie is sent
  at step 2.
- With the banner printed, it fails exactly like `f-auth-01`: the id is empty, `/regen` answers
  500, and the log says "no active session".

**Controls:**

- `php -S` keeps the session through `/regen` on every version run, on both OSes.
- Tina4's own `$request->session`, including `regenerate()`, is kept in every stock cell, on
  every version run, on both OSes.
- With debug off (3.13.141 on Linux, `cli` and `serial`), the session is lost the same way.

A hand run of the issue's exact curl sequence on stock 3.13.141 `tina4 serve` gave:

1. 200 `{"id":"","hit":null}`, with only a `tina4_session` cookie;
2. 500;
3. `{"id":"","hit":null}`.

### Why upstream's record says otherwise

- **The 3.13.99 CHANGELOG** says `headers_sent()` "is never true under `Tina4\Server`'s raw
  socket". `f6fbd8a4`'s message and its fixture's docblock repeat that premise.
- **Every stock probe here says the opposite.**
- **The bug that entry fixed** was no `tina4_session` cookie on a first login. It only happens
  while `headers_sent()` is false. Here it reproduced only under the `buffered` instrument, on
  3.11.20, 3.13.94 and 3.13.95.
- **The #253 test** (`tests/SessionRegenerateNativeCookieTest.php:61-66`, read) boots
  `App::run()` with `TINA4_SUPPRESS=true`, never through `serve`.
- **`tests/RouterSessionStartTest.php`** runs each test in a separate process. Its docblock
  says that is because `session_start()` is refused once any output has been emitted (read).
- So the tests keep headers unsent, and the real `serve` never does. Whatever setup those fixes
  were checked on most likely kept output away from PHP's output layer at boot (inferred).

## Fix for `f-auth-01` (ours, pushed to the fork, no PR)

The fix is on branch `fix/serve-leaves-headers-unsent-so-native-sessions-start`, in
`~/.cache/tina4-worktrees/php-serve-native-session`, a worktree of `gitdir/tinaforks/tina4-php`.
It was cut from upstream `v3` `44b63aee` and moved onto `0769f4fd` (3.13.142); the commits in
between change only CI files, the CHANGELOG and the version number. It is committed as
`023109ae` and pushed to the fork. There is no PR.

`fix.patch` in this directory is the same change as it stood before the commit, covering 4
files. A copy is at
`~/.cache/tina4-worktrees/php-serve-native-session.fix.patch`.

**What changes.** A new helper, `Server::console()`, writes to the `STDOUT` stream instead of
echoing, as `Log` already does. Every line the server prints while starting now goes through
it. The terminal shows the same text, but `headers_sent()` stays false, so the router's native
session starts. The converted lines are:

- `bin/tina4php`:
  - the `serve` banner;
  - the takeover `KILLED` warning;
  - the takeover refusal notice. This is `f-cli-31`'s message, the first output when debug is
    off.
- `Tina4/Server.php`: the Test Port line, both Test Port `SKIPPED` lines, and `freePort()`'s
  `KILLED` line.
- `Tina4/App.php`: `App::run()`'s five banner lines and its port-in-use notice.

**What it does not change:**

- the session code, the #253 fix, or any printed text;
- `f-cli-31`: a free port still gets the refusal notice, but the notice no longer breaks the
  session;
- a route handler's own `echo`. In one-process mode that still marks headers as sent for the
  process, but it is app output, not the server's.

**Regression test: `tests/ServeNativeSessionTest.php`, 12 cases.** Each case starts a real
server as a child process. A cookie-jar client then sets a value, regenerates the id, and
reads the value back. The cases cover:

- `serve` in 8 modes. Four setups, each run once forked per request and once as one process:
  - debug on, under the `tina4` CLI (`--managed`);
  - debug on, bare, with live reload;
  - debug on, bare, with `--no-reload`;
  - debug off, under the `tina4` CLI.
- the Test Port `SKIPPED` notice, with its port held;
- `App::run()` with its banner;
- `App::run()` with its port-in-use notice;
- reclaiming the port from a stale server. This case is skipped in two places:
  - inside a container, where takeover never signals;
  - on Windows, where takeover is broken (`f-cli-32`).

On stock `origin/v3` all 12 fail. With the fix, all 12 pass.

**Gates** (`evidence/gates.txt`):

- Reverting any one converted call turns the suite red, except G6 and G7:
  - G6 is the Test Port `SKIPPED` line for an exception;
  - G7 is `freePort()`'s `KILLED` line. It needs a bind race on Linux, because `SO_REUSEPORT`
    lets two Tina4 servers share a port.
  - No test reaches either.
- Making the helper itself echo (G10) turns all 12 red.

**Before and after, on the same app:**

- `prove.sh` on the patched tree: every cell kept, with `headers_sent` false
  (`evidence/run-fixed-*.txt`).
- A stock `tina4 init php` project under the real `tina4 serve` (CLI 3.8.94),
  `evidence/run-scaffold-fixed.txt`:
  - on stock v3 it gets no cookie, then a 500, then an empty session;
  - patched, the session survives `/regen`, and the new cookie arrives at step 2.
- Windows 11 26200, PHP 8.4.25 (`evidence/win-*-test.txt`):

  | tree | pass | fail |
  |---|---|---|
  | fix | 11 | 0 |
  | stock files swapped in | 0 | 11 |
  | fix restored | 11 | 0 |

  The reclaim case skipped in all three runs. The console text is the same with and without
  the fix.

**Upstream suite** (`evidence/suite-baseline-vs-branch.txt`): `origin/v3` and the branch fail
the same 13 tests, 12 failures and 1 error, so none of those failures is new. The branch adds
the 12 new tests. It also has one more skip, the reclaim case, because this host is a
container.

**`fix.patch` on its own:** the patch applies cleanly to a fresh `origin/v3` worktree. There,
11 cases passed, and the reclaim case also passed once it was run outside the container marker
(`evidence/run-patch-on-fresh-v3.txt`). It also applies cleanly to the staged 3.13.142
release branch (#258, `784b28f9`).

**Metrics ratchet** (#257, merged as `f77ac9cf`; `evidence/metrics-ratchet.txt`): CI's own
command, `tina4 metrics --path Tina4 --fail-on-regression` with CLI 3.8.95, passes with the
fix. There are 422 offenders before and after, and the complexity of `App.php` and
`Server.php` is unchanged.

**Residual gaps:**

- No test reaches G6 or G7.
- `console()` has a fallback for when `STDOUT` is not defined. Under the CLI that fallback
  never runs.
- Only PHP 8.4.25 was tested.
- The reclaim case was not run on Windows, by design.

**Found on the way:** on Windows, the takeover reports that it reclaimed the port but never
stops the stale server. See `../does-php-serve-reclaim-its-port-on-windows/` (`f-cli-32`).

## Bounds

- **Not run:**
  - Windows for 3.11.20, 3.13.94, 3.13.95 and v3;
  - PHP other than 8.4.25 (8.2 and 8.3 were read);
  - Apache and PHP-FPM;
  - FrankenPHP (`--production`);
  - Swoole and RoadRunner.
- **Other ways to keep headers unsent:** anything else that keeps headers unsent at boot would
  put an app in the `f-auth-02` group (inferred). Only an open `ob_start()` in `index.php`, the
  `buffered` instrument, and upstream's suppressed fixture were run.
- **App code tested:** a session started in `index.php`, not in middleware or a route. The
  reporter's app was not seen, so which group it is in is unknown.
- **Printing before the router under `php -S`** was tried as a second instance and dropped. It
  breaks every response (`http_response_code(): Cannot set response code - headers already
  sent`), not just the session.
- **Other ports:** python, ruby and nodejs have no native session module (`n/a`). Their own
  session-id rotation was not checked.
- **Not ours:**
  - The session code, the banner, the 3.13.139 change and the #253 fix are upstream's
    (`10dfbb53`, `a7b9f008`, `f6fbd8a4`).
  - Our only commit in `Router.php`, `Server.php` or `bin/tina4php` between 3.13.136 and
    3.13.141 is `d111ff45` (php#211, reload socket). It touches no output or session code.

The investigation changed nothing in the framework. Every run above names the tree it ran
against, stock or patched.

- The patched overlay used for `prove.sh` and `scaffold.sh` was deleted after the runs.
- Every server was stopped, and its port was checked free.
- Both Windows sessions deleted their guest work directory before the VM was shut down. The
  first session also deleted its Composer home.
