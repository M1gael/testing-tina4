# FIX-04 (relocated) — `tina4 test` output formatter spec

> Relocated 2026-06-30 out of `findings-log.md` (rank-9 doc cleanup). This is a speculative,
> maintainer-unrequested UI design for the `tina4 test` output formatter. The finding it
> attaches to, **PY-18-04, is CLOSED (fixed in tina4-python 3.13.4** — `tina4 test` now cleanly
> wraps pytest). Kept for reference only.

---

### FIX-04 — `tina4 test` output formatter: per-file bar, right-anchored status, bottom printer line

**Tags:** PY-18-04
**Page:** `https://tina4.com/python/18-testing.html` S1, S2, S4, S8 output
examples, plus the CLI implementation in the Rust binary.
**Status:** proposed

**The problem in one sentence.** S1's framing of `tina4 test` as having its
own readable output format was honest-on-paper but fictional in practice;
the 3.13.4 fix corrected the docs to acknowledge pytest. A real custom
formatter would let the chapter's *original* visual intent ship, and would
read better than raw pytest dots for the typical Tina4 workflow.

**Proposed layout — two modes.** Both modes share: per-file fill-bar (fills
as the file's tests complete), bottom "printer line" updating in place with
the running test ID, final failure list showing exact failing test IDs.

**Normal mode** (default): per-file row only. PASS/FAIL right-anchored to a
fixed column so status doesn't drift with varying filename widths. Bar
leftmost, filename middle. No per-file counts, no per-file times.

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ████████████░░░░░░░░  test_ch18_routes.py                                    ····
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_client_methods.py                              -
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_auth.py                                        -

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

Final state of normal mode:

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ██████░░░░░░░░░░░░░░  test_ch18_routes.py                                    FAIL
 ████████████████████  test_ch18_client_methods.py                            PASS
 ████████████████████  test_ch18_auth.py                                      PASS
 ████████████████████  test_ch18_setup_teardown.py                            PASS

──────────────────────────────────────────────────────────────────────────────────
 [████████████████████████████████]  55/59 passed  •  4 failed  •  0.33s

 Failures (4):
   FAIL  test_ch18_routes::test_get_products       AssertionError: Should return 200
   FAIL  test_ch18_routes::test_create_product     TypeError: Test.post() takes ...
   FAIL  test_ch18_routes::test_delete_product     KeyError: 'id'
   FAIL  test_ch18_routes::test_validation         AssertionError: empty body
```

**Verbose mode** (`--verbose`, see FIX-03 / PY-18-03): per-file header
unchanged in shape but adds counts (`n/m`) and per-file time on the right;
each test rendered as an indented row underneath with its own PASS/FAIL
and time. Status left-anchored on the per-file row so the indented per-test
rows line up under it.

```
========================== Tina4 test run (verbose) ==========================

 PASS   ████████████████████  test_ch18_basic.py                    3/3    0.02s
        PASS  test_addition                                                0.001s
        PASS  test_string_contains                                         0.000s
        PASS  test_array_length                                            0.001s

 PASS   ████████████████████  test_ch18_assertions.py             13/13    0.03s
        PASS  AssertEqualTest::test_equal_numbers                          0.000s
        ...

 ····   ████████████░░░░░░░░  test_ch18_routes.py                   4/6    ...
        PASS  test_health_endpoint                                         0.005s
        PASS  test_get_products                                            0.012s
        FAIL  test_create_product                                          0.008s
              TypeError: Test.post() takes 2 positional arguments but 3 given
        PASS  test_get_product_not_found                                   0.003s

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

**What each mode does and doesn't surface.**

| Element                              | Normal | Verbose |
|--------------------------------------|:------:|:-------:|
| Per-file fill-bar + PASS/FAIL        |   ✓    |    ✓    |
| Per-file counts (n/m tests)          |   ✗    |    ✓    |
| Per-file time                        |   ✗    |    ✓    |
| Per-test indented rows               |   ✗    |    ✓    |
| Per-test time                        |   ✗    |    ✓    |
| Bottom printer line (current test)   |   ✓    |    ✓    |
| Bottom failure list (exact test IDs) |   ✓    |    ✓    |

The failure list at the bottom of normal mode is the key trade-off — normal
mode hides per-test detail in the body but never hides which specific tests
failed. A reader scanning the right-hand column for `FAIL` knows which file
broke; the failure list tells them exactly which test inside.

**Rationale.**

- Right-anchored status in normal mode = the rightmost column becomes a
  fail roll-call. Eye finds failures at a fixed x-coordinate regardless of
  filename length.
- Fill-bar per file = real progress signal (fills as the file's tests run),
  not pytest's "% of total collected" which jumps unpredictably across files.
- Bottom printer line in place of file-by-file dot stream = one moving
  cursor showing the current test ID. Friendlier than the percentage
  progress at the end of each pytest file line.
- Mode split = readers who only want "did anything break" use normal;
  readers debugging a specific test use verbose. Pytest's `-q` / `-v` split
  is the same split; this is the same idea with a Tina4-native skin.

**Doc updates once implemented.** S1, S2, S4 output examples currently
show raw pytest output (post-PY-18-04 fix). Replace those with the normal-
mode mock above. S8 currently mentions `--verbose` (rejected by the CLI per
PY-18-03); once the formatter ships, the `--verbose` example should output
the verbose-mode mock above.

**Acceptance criteria.**

- `tina4 test` (default) emits the normal-mode layout: per-file bar +
  right-anchored PASS/FAIL, bottom printer line, bottom failure list with
  exact failing test IDs.
- `tina4 test --verbose` emits the verbose-mode layout: same per-file row
  but with counts + time, plus per-test indented rows.
- Both modes share the same final failure list format.
- S1, S2, S4, S8 doc examples updated to match the actual output.
- Raw pytest output remains accessible (e.g. `tina4 test --raw` or
  `uv run python -m pytest`) so users who need the underlying tool aren't
  blocked.

#### Implementation specification — exact characters, widths, and rules

This section nails down the visual primitives so an implementer can build
the formatter without guessing. Mocks above are illustrative; the rules
below are normative.

**Character set (Unicode codepoints).**

| Glyph | Codepoint | Name             | Where used                                              |
|-------|-----------|------------------|---------------------------------------------------------|
| `█`   | U+2588    | FULL BLOCK       | Bar — filled cell (per-file bar and bottom overall bar) |
| `░`   | U+2591    | LIGHT SHADE      | Bar — empty cell                                        |
| `·`   | U+00B7    | MIDDLE DOT       | "Running" status glyph (four of them: `····`)           |
| `─`   | U+2500    | BOX DRAWINGS LIGHT HORIZONTAL | Section separator above the bottom bar     |
| `=`   | U+003D    | EQUALS SIGN (ASCII) | Run header rule (`=== Tina4 test run ===`)           |
| `•`   | U+2022    | BULLET           | Inline separator in the bottom line (e.g. `26/59 • test_…`) |
| ` `   | U+0020    | SPACE            | All padding (NEVER tab / U+0009)                        |
| `-`   | U+002D    | HYPHEN-MINUS (ASCII) | Not-started status placeholder in normal mode       |

Do **not** substitute visually-similar glyphs:
- `█` ≠ `■` (U+25A0 BLACK SQUARE) — squares mis-render half-height in some terminals.
- `░` ≠ `▒` (U+2592 MEDIUM SHADE) — medium shade reads as 50% fill, not "empty".
- `·` ≠ `•` ≠ `.` — middle dot is the running glyph, bullet is the inline
  separator, full stop is never used.
- `─` ≠ `—` (em dash) ≠ `-` (hyphen-minus) — the separator must be
  U+2500 box drawing.
- ASCII `=` is correct for the header rule. Do NOT use `═` (U+2550 DOUBLE
  HORIZONTAL) — pytest uses `=` and the header reads as the Tina4 layer
  above pytest; keeping `=` reinforces continuity.

**Fallback for non-UTF8 / Windows legacy code-page terminals.** Detect
encoding at startup; if the stream can't encode U+2588/U+2591/U+00B7, fall
back to:

| Unicode | ASCII fallback |
|---------|----------------|
| `█`     | `#`            |
| `░`     | `.`            |
| `····`  | `....` (four ASCII full stops) |
| `─`     | `-`            |
| `•`     | `*`            |

No mixing — either pure-Unicode or pure-ASCII for a given run. A
`TINA4_TEST_ASCII=1` env var forces the ASCII set.

**Column widths.** Fixed for both modes. Lengths are in display cells, not
bytes (every glyph above is single-cell width — no double-wide CJK chars
in the format itself).

| Column                                | Width | Mode      |
|---------------------------------------|------:|-----------|
| Left edge gutter (space)              |   1   | both      |
| Bar                                   |  20   | both      |
| Bar→filename gutter (spaces)          |   2   | both      |
| Filename                              |  50   | both (left-padded with spaces) |
| Filename→status gutter (spaces)       |   2   | normal — status on right       |
| Status (`PASS`/`FAIL`/`····`/`-`)     |   4   | normal — right-aligned in the 4-cell slot |
| Status before bar (per-file row)      |   4   | verbose — left, *before* bar  |
| Status→bar gutter (verbose)           |   2   | verbose                       |
| n/m count                             |   5   | verbose (right-aligned, e.g. ` 3/3 `, `13/13`) |
| count→time gutter                     |   3   | verbose                       |
| Time                                  |   6   | verbose (right-aligned, e.g. `0.02s`, `0.001s`)|

Total line widths come out to 82 cells normal, 82 cells verbose — keep
them equal so the separator rule below renders the same length in both.

**Bar fill rule.**

```
filled_cells = round(20 * tests_completed_in_file / tests_total_in_file)
empty_cells  = 20 - filled_cells
bar = "█" * filled_cells + "░" * empty_cells
```

Rounding is half-to-even (banker's rounding) — avoid surprise full bars
when one test in many is still pending. If `tests_total_in_file` is
unknown during collection, render `░` × 20 with status `-`.

**Status glyph rules.**

- `PASS` — every test in the file passed.
- `FAIL` — at least one test in the file failed OR errored (collection
  error counts as FAIL on the file row).
- `····` (four U+00B7) — file currently running, at least one test started.
- `-` — file not yet started (collected but waiting).
- Status string is exactly 4 cells; right-pad with spaces if any future
  status is shorter (e.g. `OK` would render as `OK  `, never `OK`).

**Right-alignment (normal mode).** The status column ends at cell 82 of
the line. Compute:

```
status_left_edge = 82 - 4 = 78
filename_right_edge = 78 - 2 = 76   # 2-cell gutter
```

Pad filename column with trailing spaces so its right edge sits at cell 76.
For the not-started rows, render `-` right-aligned in the 4-cell slot
(`   -`) — the same column as `PASS`/`FAIL` — so the rightmost column reads
cleanly top-to-bottom.

**Bottom printer line.** Single line, rewritten in place via ANSI
`\r` + `\x1b[2K` (carriage return + erase line). No newline at end while
running. Once the run completes, emit a newline and replace with the
final summary line. Format:

```
 [<bar32>]  <done>/<total>  •  <current_test_id>
```

Where `<bar32>` is 32 cells using the same `█`/`░` chars; `<done>` and
`<total>` are integers (no padding); `<current_test_id>` is
`file_stem::class::method` (no `tests/` prefix, no `.py` suffix), truncated
to fit terminal width minus the prefix using middle-ellipsis (e.g.
`test_ch18_routes::…::test_create_product`).

**Final summary line** (replaces the printer line on completion):

```
 [████████████████████████████████]  <p> passed  •  <f> failed  •  <T>s
```

Bar always full (32 `█`). `<p>` and `<f>` are integer counts; `<T>` is
total wall-clock seconds to 2 decimal places (e.g. `0.33`). Drop the
`• <f> failed` clause entirely when `<f> == 0`.

**Failure list** (appears after the summary line, when `<f> > 0`):

```
 Failures (<f>):
   FAIL  <file_stem>::<class>::<method>   <ExceptionType>: <single-line message>
   ...
```

Rules:
- `Failures (N):` heading line, exactly one space before `Failures`.
- Each failure row: 3-space indent, `FAIL  ` (status + 2 spaces),
  test ID, 3 spaces, exception class + colon + first line of message.
- Truncate the message to keep the row at ≤ 100 cells; suffix `…` if
  truncated. Full traceback available via `--verbose` or in a written
  log file at `logs/tina4-test-<timestamp>.log`.
- No blank line between failure rows. One blank line before the heading,
  one blank line after the last row.

**Time format.**

- Per-test time (verbose only): seconds to 3 decimals, e.g. `0.001s`,
  always 5 chars + `s` = 6 cells. Under 1ms shows `0.000s` (not `<0.001s`).
- Per-file time (verbose only): seconds to 2 decimals, e.g. `0.02s`,
  always 4 chars + `s` = 5 cells (allow up to 99.99s; over that, switch to
  `XXm` for whole minutes with no decimals).
- Total run time (summary): same as per-file but unbounded — render
  `0.33s`, `12.45s`, `1m23s`, `5m04s` as the magnitude requires.

**Colour scheme** (when stdout is a TTY and `NO_COLOR` env var is unset):

| Element                            | ANSI                                |
|------------------------------------|-------------------------------------|
| `PASS`                             | bright green (`\x1b[92m`)           |
| `FAIL`                             | bright red (`\x1b[91m`)             |
| `····` running                     | bright yellow (`\x1b[93m`)          |
| `-` not started                    | dim grey (`\x1b[2m\x1b[37m`)        |
| Bar filled cells                   | inherit terminal default (no colour) |
| Bar empty cells                    | dim grey                            |
| Bottom bar filled                  | inherit                             |
| Filename                           | inherit                             |
| Failure rows `FAIL` glyph + ID     | bright red                          |
| Failure exception line             | inherit                             |
| Run header / separator rules       | dim grey                            |

When `NO_COLOR` is set, or stdout is not a TTY, emit plain ASCII/Unicode
with no escape sequences. The fallback in this case is the same layout —
colour is decorative only.

**Indentation in verbose mode per-test rows.** 8 spaces (matches the
length of the per-file row's "status + gutter + bar start"), then 4-cell
`PASS`/`FAIL` (left-aligned), then 2-space gutter, then test name
(class-qualified), then padding to time column. Time format same as
per-file time but 3 decimals (per-test rule above).

**Things to NOT do (anti-patterns seen elsewhere):**

- Don't use ANSI cursor-up to overwrite the per-file rows — the running
  file's row gets its bar updated in place, but completed rows above
  must stay put. Use a single bottom-line cursor pattern only.
- Don't right-trim trailing whitespace on a row before emitting it —
  the trailing spaces are load-bearing for the right-aligned status
  column. Trimming breaks alignment in terminals that auto-trim.
- Don't print the run header until after collection completes — the
  count `26/59` in the printer line needs the total. Show a single-line
  "Collecting tests…" stub during collection, then redraw.
- Don't substitute the four middle dots `····` with three (`···`) or an
  ellipsis `…` — the running glyph is always exactly 4 cells to match
  `PASS`/`FAIL` width.
- Don't render the per-file bar live-updating cell-by-cell as each test
  finishes if the file completes in under 100 ms — the flicker reads as
  glitchy. Batch updates at 100 ms minimum cadence, or render the file
  row only on file completion if the whole file ran under that threshold.

---
