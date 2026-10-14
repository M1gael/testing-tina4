# A repeated multipart `name[]` field keeps only its last value

Ledger `f-rt-05`. Upstream issues (a teammate's): tina4-php#294, tina4-python#214, tina4-nodejs#131.

A form posting `tags[]=red` and `tags[]=blue` (a multi-select or checkbox group) parses to
`{"tags[]": "blue"}`. The reports say only multipart is affected. Running it showed urlencoded
bodies are broken too in Ruby and Node.js, and the query string differs per port.

## What each port does (stock, v3 tips 2026-10-13)

py `005f03a1`, php `0a453208`, rb `0c8f3b5`, nd `b2078dc`. Results are from `out-tip.txt`.

| | multipart body | urlencoded body | query string |
|---|---|---|---|
| python | `tags[]`: last only | `tags[]`: list, raw key | `tags[]`: list, raw key |
| php (`tina4php serve`) | `tags[]`: last only | nested (`parse_str`) | nested (`parse_str`) |
| ruby | nested (`FormParser`) | `tags[]`: last only | `tags[]`: last only |
| nodejs | `tags[]`: last only | `tags[]`: last only | `tags[]`: last only |

## Mechanism

- py: the multipart text branch assigns by raw name, `tina4_python/core/request.py:634`. The
  urlencoded branch uses `parse_qs` and keeps the raw key, `:522`.
- php: the multipart text branch assigns by raw name, `Tina4/Server.php:2838` (`parseMultipartBody`,
  called at `:1326` and from `Request.php:609`).
- rb: the urlencoded body goes through `parse_query_to_hash`, which splits on `&` and keeps the last
  value per raw key, `lib/tina4/request.rb:587`.
- nd: both bodies assign by raw name, `packages/core/src/request.ts:277` (urlencoded) and `:362`
  (multipart).

## Fix (user chose: request bodies, PHP/Rack shape; query string left flat)

The query string stays flat because AutoCrud reads `filter[...]` keys from it in py, rb and nd.

Branch `fix/a-bracketed-form-field-arrives-as-a-list`, worktrees `~/.cache/tina4-worktrees/frt05-*`.
The diffs are saved as `frt05-*.fix.patch` next to them.

- **py:** both bodies go through a port of tina4-ruby's `normalize_params`. A repeated plain name
  stays a list, which is py's existing urlencoded behaviour. A real upload is told apart from a
  nested text dict by its `bytes` content.
- **php:** a small bracket walker replaces raw assignment. It follows `parse_str` semantics without
  the `max_input_vars` cut-off and without renaming `.` and spaces. `parse_str` itself was tried
  first and dropped: it lost every field past 1000 and renamed `a.b c` to `a_b_c`, where stock keeps
  both.
- **rb:** the urlencoded body uses `FormParser.nest`, the code multipart already used, in a
  lenient mode: a name that is not valid UTF-8 keeps its flat key instead of raising.
- **nd:** both bodies go through a port of `normalize_params`. A `__proto__` segment is dropped,
  and own-property checks let names such as `toString[]` nest.
- **Limits, every port:** a field whose name conflicts with an earlier one keeps its flat key
  while the rest still nest. php overwrites instead, as `parse_str` does. A name 32 or more levels
  deep or longer than 1024 bytes keeps its flat key, and a body with more than 4096 fields does
  not nest at all (Rack's limits, plus the name cap). A later plain name replaces an earlier nested
  value of that name, as Rack and `parse_str` do; py joins it onto a list. Measured peaks at that cap under a crafted depth-31 name: py 80MB, nd 31MB heap, php
  +52MB, rb 95MB.
- **py:** `photo[caption]` beside a `photo` upload keeps its flat key.
- **php:** the `a[9223372036854775807]` then `a[]` overflow keeps the second field flat; an
  earlier version of this fix threw a fatal error there (stock never nests, so it never did).

## Run

`URLENC=1 ./prove.sh` posts with curl to each port's real server (`tina4php serve` needs
`TINA4_OVERRIDE_CLIENT=true`). Trees default to stock under `~/.cache/tina4-worktrees/tip-stock-*`;
`PY= PHP= RB= ND=` override them and `ONLY=` narrows the run. Stock output is in `out-tip.txt`
(3 BUG), the fix output in `out-fix.txt` (0 BUG). `php php/parse-direct.php <tree>` calls the
parser alone.
