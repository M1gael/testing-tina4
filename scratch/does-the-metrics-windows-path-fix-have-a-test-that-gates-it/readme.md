# Does tina4-php PR #210's regression test gate the Windows branch?

No. The defect and the fix are both right; the test that ships with them is green either way on
the only OS the CI runs.

Run against: tina4-php PR #210 head `af20d422`, base `origin/v3` `e0df3a97`, PHP 8.4.25, Linux.

## The defect (confirmed by reading — the failure itself is Windows-only)

`Tina4/Metrics.php:44-46` at `origin/v3`:

```php
$which = PHP_OS_FAMILY === "Windows" ? "where" : "command -v";
$output = @shell_exec("$which tina4 2>/dev/null");
```

The lookup command is OS-selected. The redirect is not. `shell_exec` on Windows goes through
`cmd.exe /c`, which resolves redirection targets before running the command, so `2>/dev/null`
is read as a path `\dev\null`, fails, and `where` never runs. Empty output, `enginePath()`
returns null, `runEngine()` throws `"tina4 not found on PATH"` — the 503 on the Metrics tab,
with the CLI installed and on PATH.

The same file family already has the correct form: `Tina4/AITools.php:926` uses
`PHP_OS_FAMILY === 'Windows' ? "where {$command} 2>NUL" : "which {$command} 2>/dev/null"`.

## The test does not gate it

PR #210 adds `tests/MetricsEnginePathTest.php`, which reflects into the new
`Metrics::locateOnPath()` and asserts a known-present binary resolves (`sh` on Unix, `where` on
Windows) and an absent one returns null.

On Linux both assertions hold with **or** without the fix, because `2>/dev/null` was always
correct there. Mutation — delete the Windows arm, keep the method:

```php
$discard = "2>/dev/null"; // MUTATION
```

```
## as submitted          OK (2 tests, 3 assertions)
## Windows arm deleted   OK (2 tests, 3 assertions)
```

`./prove.sh` reproduces this.

It is not merely that the test is weak on Linux — **the Windows arm is executed nowhere in CI**.
`.github/workflows/` at `origin/v3` declares `runs-on:` seven times, `ubuntu-latest` every time.
So "Linux CI green" is not evidence about this fix, and the test only turns red on unfixed source
by `ReflectionException: Method Tina4\Metrics::locateOnPath() does not exist` — it gates the
method's existence, not its behaviour.

A test that does gate it needs the OS out of the environment and into an argument, e.g. a
`nullRedirect(string $osFamily): string` asserted as `2>nul` for `"Windows"` and `2>/dev/null`
otherwise. That runs on Linux and turns red the moment the Windows arm is touched.

## Six more instances of the same defect, unfixed, in the same repo

Same shape: a shelled-out command with a hardcoded `2>/dev/null`, no `PHP_OS_FAMILY` guard, all
reachable on Windows through the same dev-admin surface.

| | |
|---|---|
| `Tina4/DevAdmin.php:1996` | `cd <root> && git status --porcelain 2>/dev/null` |
| `Tina4/DevAdmin.php:2792` | `cd <root> && git rev-parse --abbrev-ref HEAD 2>/dev/null` |
| `Tina4/DevAdmin.php:2809` | `cd <root> && git rev-parse --show-toplevel 2>/dev/null` |
| `Tina4/DevAdmin.php:2861` | `cd <root> && git status --porcelain -uall 2>/dev/null` |
| `Tina4/Bootstrap/MCP.php:2121` | `cd <root> && git rev-parse --is-inside-work-tree 2>/dev/null` |

`Tina4/PortTakeover.php:187` (`lsof -ti`) is **not** one of them — it is guarded by a Windows
branch at `:171`.

Those five carry a second Windows fault in the same string: `cd <path>` without `/d` does not
change drive on cmd.exe, so even with the redirect fixed the command would run in the wrong
directory whenever the project is on a drive other than the shell's.

## Cross-port

Checked `tina4-python`, `tina4-ruby`, `tina4-nodejs` at `origin/v3`: no equivalent PATH lookup
for the CLI binary, so this instance is PHP-only. One nearby lead, not investigated:
`tina4-nodejs packages/core/src/ai.ts:259` and `:490` call `execSync("which ...")`, and `which`
is not a cmd.exe command — a different mechanism with the same "feature reads as absent on
Windows" symptom.

## Bounds

- Everything about cmd.exe's behaviour here is read, not run: there is no Windows machine in this
  environment. @ChanBos verified the fix on Windows.
- The mutation result is measured, on Linux, on the PR head.
- The six sibling instances are identified by reading. None was executed on Windows.
